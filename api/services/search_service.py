"""Unified search service orchestrating vector search, filtering, and reranking."""

import time
from typing import AsyncGenerator

from api.core.config import Settings
from api.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    StreamingSearchEvent,
)
from api.vector_db.qdrant_manager import QdrantManager
from api.vector_db.medcpt_encoder import MedCPTEncoder
from api.services.reranking_service import RerankingService


class SearchService:
    """Orchestrates search across vector DB with reranking."""

    def __init__(self, config: Settings):
        self.config = config
        self._qdrant: QdrantManager | None = None
        self._encoder: MedCPTEncoder | None = None
        self._reranker = RerankingService()

    async def initialize(self) -> None:
        """Initialize connections and models."""
        self._encoder = MedCPTEncoder()
        await self._encoder.load()

        self._qdrant = QdrantManager(
            host=self.config.qdrant_host,
            port=self.config.qdrant_port,
            url=self.config.qdrant_url,
            api_key=self.config.qdrant_apikey,
            collection_name=self.config.qdrant_collection_name,
            timeout=self.config.qdrant_timeout_seconds,
        )
        await self._qdrant.connect()

    async def close(self) -> None:
        """Close connections."""
        if self._qdrant:
            await self._qdrant.close()

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Execute search with optional reranking.

        Flow:
        1. Encode query using MedCPT
        2. Search Qdrant for vector matches
        3. Apply lexical filtering
        4. Apply hybrid reranking
        5. Return ranked results
        """
        start_time = time.time()

        # Encode query
        query_embedding = self._encoder.encode_queries([request.query], show_progress=False)

        # Build filters
        filters = self._build_filters(request)

        # Search Qdrant (over-fetch for reranking)
        oversample_limit = request.limit * 3
        raw_results = await self._qdrant.search(
            query_vector=query_embedding[0].tolist(),
            limit=oversample_limit,
            filters=filters,
        )

        # Convert to SearchResult models
        results = [self._to_search_result(r) for r in raw_results]

        # Apply reranking if enabled
        if request.use_reranking:
            results = self._reranker.rerank(
                query=request.query,
                results=results,
                lexical_min=request.lexical_min if request.use_lexical_filter else 0.0,
            )

        # Limit to requested count
        results = results[:request.limit]

        # Assess evidence quality
        evidence_quality = self._reranker.assess_evidence_quality(results)

        elapsed_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=request.query,
            results=results,
            total_found=len(results),
            evidence_quality=evidence_quality,
            search_time_ms=elapsed_ms,
        )

    async def search_streaming(
        self,
        request: SearchRequest,
    ) -> AsyncGenerator[StreamingSearchEvent, None]:
        """Stream search results as they become available."""
        try:
            yield StreamingSearchEvent(event_type="status", data="Starting search...")

            response = await self.search(request)

            for result in response.results:
                yield StreamingSearchEvent(event_type="result", data=result)

            yield StreamingSearchEvent(
                event_type="done",
                data={
                    "total": response.total_found,
                    "evidence_quality": response.evidence_quality,
                    "search_time_ms": response.search_time_ms,
                },
            )
        except Exception as e:
            yield StreamingSearchEvent(event_type="error", data=str(e))

    def _build_filters(self, request: SearchRequest) -> dict:
        """Build Qdrant filter from request parameters."""
        filters = {}

        if request.year_from:
            filters["year_gte"] = request.year_from
        if request.year_to:
            filters["year_lte"] = request.year_to
        if request.min_citations:
            filters["citations_gte"] = request.min_citations
        if request.publication_types:
            filters["publication_types"] = request.publication_types

        return filters

    def _to_search_result(self, raw: dict) -> SearchResult:
        """Convert raw Qdrant result to SearchResult model."""
        payload = raw.get("payload", {})
        
        # Extract authors - handle both string list and object list formats
        authors_raw = payload.get("authors", [])
        authors = []
        if isinstance(authors_raw, list):
            for author in authors_raw:
                if isinstance(author, str):
                    authors.append(author)
                elif isinstance(author, dict):
                    # Handle author objects with 'name' field
                    name = author.get("name", "")
                    if name:
                        authors.append(name)
        
        # Extract DOI from external_ids
        doi = None
        external_ids = payload.get("external_ids") or payload.get("externalids")
        if external_ids:
            doi_obj = external_ids.get("DOI") or external_ids.get("doi")
            if isinstance(doi_obj, dict):
                doi = str(doi_obj.get("value", "")) or str(doi_obj) if doi_obj else None
            else:
                doi = str(doi_obj) if doi_obj else None
        
        # Extract publication types
        pub_types = payload.get("publication_types") or payload.get("publicationtypes")
        publication_type = None
        if pub_types and isinstance(pub_types, list) and len(pub_types) > 0:
            publication_type = ", ".join(pub_types)
        
        return SearchResult(
            paper_id=payload.get("paper_id", "") or str(raw.get("id", "")),
            title=payload.get("title", ""),
            abstract=payload.get("abstract"),
            authors=authors,
            year=payload.get("year"),
            citation_count=payload.get("citation_count") or payload.get("citationcount"),
            publication_type=publication_type,
            doi=doi,
            url=payload.get("url"),
            vector_score=raw.get("score", 0.0),
            source="qdrant",
        )

