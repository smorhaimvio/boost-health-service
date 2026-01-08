"""Hybrid reranking service combining vector, lexical, and metadata scores."""

from api.models import SearchResult
from api.vector_db.lexical_filter import compute_lexical_score


class RerankingService:
    """Service for reranking search results using hybrid scoring."""

    def __init__(
        self,
        lexical_weight: float = 0.2,
        recency_bonus_2018: float = 0.2,
        recency_bonus_2022: float = 0.2,
        citation_bonus_50: float = 0.2,
        citation_bonus_10: float = 0.1,
    ):
        self.lexical_weight = lexical_weight
        self.recency_bonus_2018 = recency_bonus_2018
        self.recency_bonus_2022 = recency_bonus_2022
        self.citation_bonus_50 = citation_bonus_50
        self.citation_bonus_10 = citation_bonus_10

    def compute_metadata_bonus(self, result: SearchResult) -> float:
        """Compute metadata-based bonus score."""
        bonus = 0.0

        if result.year:
            if result.year >= 2022:
                bonus += self.recency_bonus_2022
            elif result.year >= 2018:
                bonus += self.recency_bonus_2018

        if result.citation_count:
            if result.citation_count >= 50:
                bonus += self.citation_bonus_50
            elif result.citation_count >= 10:
                bonus += self.citation_bonus_10

        return bonus

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        lexical_min: float = 0.05,
    ) -> list[SearchResult]:
        """
        Rerank results using hybrid scoring.

        Combines:
        - Vector similarity score (from Qdrant)
        - Lexical overlap score
        - Metadata bonus (recency, citations)

        Filters by minimum lexical threshold.
        """
        reranked = []

        for result in results:
            # Compute lexical score
            lexical_score = compute_lexical_score(
                query=query,
                title=result.title,
                abstract=result.abstract,
            )

            # Filter by lexical minimum
            if lexical_score < lexical_min:
                continue

            # Compute metadata bonus
            meta_bonus = self.compute_metadata_bonus(result)

            # Combine scores
            combined = result.vector_score + self.lexical_weight * (lexical_score + meta_bonus)

            # Update result with scores
            result.lexical_score = lexical_score
            result.combined_score = combined

            reranked.append(result)

        # Sort by combined score (descending)
        reranked.sort(key=lambda r: r.combined_score, reverse=True)

        return reranked

    def assess_evidence_quality(
        self,
        results: list[SearchResult],
    ) -> int:
        """Assess overall evidence quality of results on a 0-5 scale.
        
        Quality Score Criteria:
        5 - Exceptional: Multiple systematic reviews/meta-analyses, high citations
        4 - Strong: Mix of reviews and high-quality RCTs, good citations
        3 - Moderate: Several primary studies with decent citations
        2 - Limited: Few studies or lower quality evidence
        1 - Weak: Very limited evidence, low citations
        0 - Insufficient: No relevant results
        
        Args:
            results: List of search results to assess
            
        Returns:
            Quality score from 0 to 5
        """
        if not results:
            return 0
        
        # Count evidence types
        meta_analyses = 0
        systematic_reviews = 0
        rcts = 0
        other_reviews = 0
        high_citation_studies = 0  # >100 citations
        moderate_citation_studies = 0  # 50-100 citations
        recent_studies = 0  # Last 3 years
        
        for result in results:
            pub_type = (result.publication_type or "").lower()
            citations = result.citation_count or 0
            year = result.year or 0
            current_year = 2025  # Update as needed
            
            # Categorize by publication type
            if "meta-analysis" in pub_type or "meta analysis" in pub_type:
                meta_analyses += 1
            elif "systematic review" in pub_type:
                systematic_reviews += 1
            elif "randomized controlled trial" in pub_type or "rct" in pub_type:
                rcts += 1
            elif "review" in pub_type:
                other_reviews += 1
            
            # Citation counts
            if citations >= 100:
                high_citation_studies += 1
            elif citations >= 50:
                moderate_citation_studies += 1
            
            # Recency
            if year >= current_year - 3:
                recent_studies += 1
        
        # Calculate quality score
        score = 0
        
        # Base score from number of results
        if len(results) >= 5:
            score += 1
        elif len(results) >= 3:
            score += 0.5
        
        # Evidence hierarchy (most important)
        if meta_analyses >= 2:
            score += 2.5
        elif meta_analyses >= 1:
            score += 2.0
        elif systematic_reviews >= 2:
            score += 2.0
        elif systematic_reviews >= 1:
            score += 1.5
        elif rcts >= 3:
            score += 1.5
        elif rcts >= 1:
            score += 1.0
        elif other_reviews >= 2:
            score += 1.0
        elif other_reviews >= 1:
            score += 0.5
        
        # Citation impact
        if high_citation_studies >= 2:
            score += 1.0
        elif high_citation_studies >= 1:
            score += 0.5
        elif moderate_citation_studies >= 2:
            score += 0.5
        
        # Recency bonus (current evidence)
        if recent_studies >= 2:
            score += 0.5
        
        # Cap at 5
        return min(5, round(score))

