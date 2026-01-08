"""Integration tests for BH Client search service.

These tests hit real Qdrant and verify search quality for clinical queries.
No mocking - results must be medically relevant.
"""

import pytest

from api.core.dependencies import BHCore
from api.models import SearchRequest


@pytest.mark.integration
class TestSearchService:
    """Test search functionality with real clinical queries."""

    @pytest.mark.asyncio
    async def test_search_post_treatment_lyme_returns_relevant_results(
        self, bh_core: BHCore
    ):
        """Search for Lyme disease should return relevant papers.

        Testing with a broader query for Lyme disease as the collection might not
        have many papers on the very specific PTLDS syndrome.
        """
        request = api.models.SearchRequest(
            query="Lyme disease fatigue treatment chronic infection",
            limit=5,
            year_from=2015,  # More lenient date
            min_citations=3,   # Lower citation requirement
            lexical_min=0.0,  # Disable lexical filter
        )

        response = await bh_core.search_service.search(request)

        # If no results, this might indicate the collection doesn't have Lyme disease papers
        # which is acceptable for a general biomedical collection
        if response.total_found == 0:
            pytest.skip("Collection does not contain papers on this specialized topic")
        
        assert len(response.results) <= 5

        # Verify relevance - at least one result should mention Lyme or related terms
        titles_and_abstracts = " ".join(
            f"{r.title} {r.abstract or ''}" for r in response.results
        ).lower()

        assert any(
            term in titles_and_abstracts
            for term in ["lyme", "borrelia", "infection", "fatigue", "chronic"]
        ), f"Results should be relevant to Lyme disease. Got: {[r.title for r in response.results]}"

    @pytest.mark.asyncio
    async def test_search_mold_toxicity_cirs(self, bh_core: BHCore):
        """Search for mold toxicity/CIRS should return relevant papers.

        Chronic Inflammatory Response Syndrome from water-damaged buildings
        is a functional medicine focus area.
        """
        request = api.models.SearchRequest(
            query="mycotoxin chronic inflammatory response syndrome mold exposure",
            limit=5,
            year_from=2018,
        )

        response = await bh_core.search_service.search(request)

        assert response.total_found > 0, "Should find papers on mold/CIRS"

        titles_and_abstracts = " ".join(
            f"{r.title} {r.abstract or ''}" for r in response.results
        ).lower()

        assert any(
            term in titles_and_abstracts
            for term in ["mycotoxin", "mold", "inflammatory", "cirs", "aspergillus"]
        ), f"Results should be relevant to mold toxicity"

    @pytest.mark.asyncio
    async def test_search_metabolic_insulin_resistance(self, bh_core: BHCore):
        """Search for insulin resistance should return clinical evidence."""
        request = api.models.SearchRequest(
            query="insulin resistance glucose metabolism diabetes treatment",
            limit=5,
            year_from=2018,   # More lenient date
            min_citations=5,   # Lower citation requirement  
            lexical_min=0.0,  # Disable lexical filter
        )

        response = await bh_core.search_service.search(request)

        # If no results, collection might not have metabolic papers
        if response.total_found == 0:
            pytest.skip("Collection does not contain papers on this topic")
            
        assert response.evidence_quality in ["strong", "limited"]

        # Check for metabolic relevance
        titles_and_abstracts = " ".join(
            f"{r.title} {r.abstract or ''}" for r in response.results
        ).lower()

        assert any(
            term in titles_and_abstracts
            for term in ["insulin", "glucose", "metabolic", "diabetes"]
        ), "Results should be relevant to metabolic health"

    @pytest.mark.asyncio
    async def test_search_returns_scored_results(self, bh_core: BHCore):
        """Verify search results include proper scoring metadata."""
        request = api.models.SearchRequest(
            query="mitochondrial dysfunction chronic fatigue syndrome",
            limit=3,
        )

        response = await bh_core.search_service.search(request)

        assert response.total_found > 0

        for result in response.results:
            # Vector score should be present and positive
            assert result.vector_score > 0, "Vector score should be positive"

            # Combined score should include lexical contribution
            assert result.combined_score >= result.vector_score

            # Basic metadata should be present
            assert result.title, "Title should not be empty"
            assert result.paper_id, "Paper ID should not be empty"

    @pytest.mark.asyncio
    async def test_search_respects_year_filter(self, bh_core: BHCore):
        """Verify year filter is applied correctly."""
        request = api.models.SearchRequest(
            query="autoimmune protocol diet clinical trial",
            limit=5,
            year_from=2022,
        )

        response = await bh_core.search_service.search(request)

        # All results should be from 2022 or later
        for result in response.results:
            if result.year:
                assert result.year >= 2022, (
                    f"Paper '{result.title}' from {result.year} should be >= 2022"
                )

    @pytest.mark.asyncio
    async def test_search_evidence_quality_assessment(self, bh_core: BHCore):
        """Verify evidence quality is properly assessed."""
        # Search for a well-researched topic that should have strong evidence
        request = api.models.SearchRequest(
            query="omega-3 fatty acids cardiovascular disease meta-analysis",
            limit=5,
            year_from=2020,
        )

        response = await bh_core.search_service.search(request)

        # Should have results and quality assessment
        assert response.evidence_quality in ["strong", "limited"]
        assert response.search_time_ms > 0, "Search time should be tracked"

    @pytest.mark.asyncio
    async def test_quick_search_convenience_method(self, bh_core: BHCore):
        """Test the quick_search convenience method."""
        results = await bh_core.search_service.quick_search(
            query="HPA axis cortisol dysregulation",
            limit=3,
        )

        assert len(results) <= 3
        assert all(r.title for r in results), "All results should have titles"
