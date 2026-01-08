"""Qdrant client manager for storing and searching documents."""

import hashlib
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Range,
    VectorParams,
)

from tqdm import tqdm


class QdrantManager:
    """Manager for Qdrant operations."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "semantic_scholar_papers",
        url: str | None = None,
        api_key: str | None = None,
        timeout: float = 600.0,
    ):
        """
        Initialize Qdrant client.

        Args:
            host: Qdrant server host (for local connection)
            port: Qdrant server port (for local connection)
            collection_name: Name of the collection to use
            url: Qdrant cloud URL (e.g., https://xxxxxx-xxxxx-xxxxx-xxxx-xxxxxxxxx.us-east.aws.cloud.qdrant.io:6333)
            api_key: Qdrant API key for cloud connection
            timeout: Timeout in seconds for Qdrant operations (default: 600 seconds = 10 minutes)
        """
        # If API key is provided, use cloud connection with URL
        if api_key and url:
            self.client = QdrantClient(
                url=url, 
                api_key=api_key, 
                timeout=timeout,
                check_compatibility=False  # Skip version check to avoid warnings
            )
            self.collection_name = collection_name
            print(f"Connected to Qdrant cloud at {url}")
        else:
            # Otherwise, use local connection
            self.client = QdrantClient(
                host=host, 
                port=port, 
                timeout=timeout,
                check_compatibility=False
            )
            self.collection_name = collection_name
            print(f"Connected to Qdrant at {host}:{port}")

    async def connect(self) -> None:
        """Async connect method for compatibility."""
        pass

    async def close(self) -> None:
        """Close Qdrant connection."""
        pass

    @staticmethod
    def make_doc_key(paper: dict) -> str:
        """
        Generate a canonical document key using priority:
        1. Semantic Scholar paperId (always present, globally unique)
        2. DOI if present
        3. Hash of title + year as fallback

        Args:
            paper: Paper dictionary

        Returns:
            Canonical document key string
        """
        if paper.get("paperId"):
            return f"s2:{paper['paperId']}"
        if paper.get("doi"):
            return f"doi:{paper['doi'].lower()}"
        title = (paper.get("title") or "").strip().lower()
        year = str(paper.get("year") or "")
        return "ty:" + hashlib.sha1(f"{title}|{year}".encode("utf-8")).hexdigest()

    def create_collection(
        self,
        vector_size: int,
        distance: Distance = Distance.COSINE,
        recreate: bool = False,
    ):
        """
        Create a collection for storing paper embeddings.

        Args:
            vector_size: Dimension of the embeddings
            distance: Distance metric (COSINE, DOT, EUCLID)
            recreate: Whether to recreate if collection exists
        """
        # Check if collection exists
        exists = self.collection_exists()

        if recreate and exists:
            try:
                self.client.delete_collection(self.collection_name)
                print(f"Deleted existing collection: {self.collection_name}")
                exists = False
            except Exception as e:
                print(f"Error deleting collection: {e}")
                return

        if not exists:
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                )
                print(f"Created collection: {self.collection_name}")
                print(f"Vector size: {vector_size}, Distance: {distance}")
            except Exception as e:
                print(f"Error creating collection: {e}")
        else:
            print(
                f"Collection '{self.collection_name}' already exists, using existing collection"
            )

    def collection_exists(self) -> bool:
        """Check if the collection exists."""
        try:
            collections = self.client.get_collections()
            return any(
                col.name == self.collection_name for col in collections.collections
            )
        except Exception:
            return False

    def get_collection_info(self) -> Dict:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            return {"error": str(e)}

    def prepare_paper_payload(self, paper: Dict) -> Dict[str, Any]:
        """
        Prepare paper metadata for storage.

        Args:
            paper: Paper dictionary from Semantic Scholar

        Returns:
            Payload dictionary for Qdrant
        """
        payload = {
            "paper_id": paper.get("paperId", ""),
            "title": paper.get("title", ""),
            "abstract": paper.get("abstract", ""),
            "year": paper.get("year"),
            "citation_count": paper.get("citationCount", 0),
            "url": paper.get("url", ""),
        }

        # Handle journal
        journal = paper.get("journal")
        if journal:
            payload["journal_name"] = (
                journal.get("name", "") if isinstance(journal, dict) else str(journal)
            )

        # Handle publication types
        pub_types = paper.get("publicationTypes", [])
        if pub_types:
            payload["publication_types"] = pub_types

        # Handle authors
        authors = paper.get("authors", [])
        if authors:
            payload["authors"] = [
                author.get("name", "") if isinstance(author, dict) else str(author)
                for author in authors
            ]

        # Handle external IDs
        external_ids = paper.get("externalIds", {})
        if external_ids:
            payload["external_ids"] = external_ids

        return payload

    def index_papers(
        self,
        papers: List[Dict],
        embeddings: List[List[float]],
        batch_size: int = 100,
    ):
        """
        Index papers into Qdrant.

        Args:
            papers: List of paper dictionaries
            embeddings: List of embedding vectors
            batch_size: Batch size for uploading
        """
        if len(papers) != len(embeddings):
            raise ValueError("Number of papers must match number of embeddings")

        points = []

        print("Preparing points for indexing...")

        for paper, embedding in tqdm(zip(papers, embeddings), total=len(papers)):
            # Generate canonical document key for deduplication
            doc_key = self.make_doc_key(paper)

            # Convert doc_key to UUID (Qdrant requires UUID or int as point ID)
            # Use UUID5 with DNS namespace for deterministic UUID from doc_key
            # This ensures the same doc_key always produces the same UUID
            namespace = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
            point_id = str(uuid.uuid5(namespace, doc_key))

            # Prepare payload
            payload = self.prepare_paper_payload(paper)
            # Store doc_key in payload for transparency and future deduplication
            payload["doc_key"] = doc_key

            # Use deterministic UUID as the Qdrant point ID
            # This ensures automatic deduplication via upsert
            point = PointStruct(
                id=point_id,
                vector=(
                    embedding.tolist() if hasattr(embedding, "tolist") else embedding
                ),
                payload=payload,
            )
            points.append(point)

        # Upload in batches
        print(f"Uploading {len(points)} points to Qdrant...")

        for i in tqdm(range(0, len(points), batch_size), desc="Uploading batches"):
            batch = points[i : i + batch_size]
            self.client.upsert(  # upsert = insert or update if exists
                collection_name=self.collection_name, points=batch
            )

        print(f"Successfully indexed {len(points)} papers!")
        print("Note: upsert mode - duplicates are automatically updated, not re-added")
        return len(points)

    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: dict | None = None,
    ) -> List[Dict]:
        """
        Search for similar papers.

        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            filters: Dictionary of filters (year_gte, year_lte, citations_gte, publication_types)

        Returns:
            List of search results with papers and scores
        """
        filters = filters or {}

        # Build filter conditions
        filter_conditions = []

        if "year_gte" in filters:
            filter_conditions.append(
                FieldCondition(key="year", range=Range(gte=filters["year_gte"]))
            )

        if "year_lte" in filters:
            filter_conditions.append(
                FieldCondition(key="year", range=Range(lte=filters["year_lte"]))
            )

        if "citations_gte" in filters:
            filter_conditions.append(
                FieldCondition(key="citationcount", range=Range(gte=filters["citations_gte"]))
            )

        if "publication_types" in filters:
            for pub_type in filters["publication_types"]:
                filter_conditions.append(
                    FieldCondition(
                        key="publicationtypes", match=MatchValue(value=pub_type)
                    )
                )

        # Create filter if we have conditions
        search_filter = None
        if filter_conditions:
            search_filter = Filter(must=filter_conditions)

        # Use query_points() for qdrant-client >= 1.7.0
        # The 'query' parameter takes the vector directly
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=search_filter,
            limit=limit,
            with_payload=True,
        )

        # Format results - query_points returns QueryResponse with .points
        formatted_results = []
        for point in search_results.points:
            formatted_results.append({
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload
            })

        return formatted_results

    def count_papers(self) -> int:
        """Get the total number of papers in the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception as e:
            print(f"Error counting papers: {e}")
            return 0

