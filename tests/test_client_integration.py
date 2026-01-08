"""End-to-end integration tests for BH Client.

These tests verify the complete client functionality against real services.
Focus on clinical use cases that would be used in production.
"""

import pytest

from api.core.dependencies import BHCore
from api.models import SearchRequest


@pytest.mark.integration
class TestBHCoreIntegration:
    """End-to-end tests for the BH Client."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Client should work as async context manager."""
        async with BHCore() as client:
            results = await client.quick_search(
                query="gut microbiome dysbiosis",
                limit=2,
            )
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_client_initialization_and_cleanup(self):
        """Client should properly initialize and cleanup resources."""
        client = BHCore()

        # Should not be initialized yet
        assert not client._initialized

        await client.initialize()
        assert client._initialized

        # Should be able to search
        results = await client.quick_search("methylation MTHFR", limit=2)
        assert len(results) > 0

        await client.close()
        assert not client._initialized

    @pytest.mark.asyncio
    async def test_full_search_workflow_functional_medicine(
        self, bh_core: BHCore
    ):
        """Complete search workflow for functional medicine query."""
        # Complex functional medicine query
        request = api.models.SearchRequest(
            query=(
                "chronic inflammatory response syndrome CIRS mold exposure "
                "biotoxin illness treatment cholestyramine"
            ),
            limit=5,
            year_from=2018,
            min_citations=3,
            use_reranking=True,
            use_lexical_filter=True,
            lexical_min=0.03,
        )

        response = await bh_core.search_service.search(request)

        # Verify response structure
        assert response.query == request.query
        assert response.total_found >= 0
        assert response.evidence_quality in ["strong", "limited"]
        assert response.search_time_ms > 0

        # If results found, verify quality
        if response.results:
            for result in response.results:
                assert result.title
                assert result.paper_id
                assert result.vector_score > 0
                assert result.combined_score >= result.vector_score

    @pytest.mark.asyncio
    async def test_search_and_intent_extraction_together(
        self, bh_core: BHCore
    ):
        """Test running search and intent extraction concurrently."""
        import asyncio

        query = "post-treatment Lyme disease persistent symptoms fatigue"

        # Run both operations concurrently (as would happen in real usage)
        search_task = bh_core.search_service.search(
            api.models.SearchRequest(query=query, limit=3)
        )
        intent_task = bh_core.search_service.extract_intent(query)

        search_response, intent = await asyncio.gather(
            search_task, intent_task
        )

        # Both should complete successfully
        assert search_response.total_found >= 0
        assert intent.get("task_type")

    @pytest.mark.asyncio
    async def test_search_mitochondrial_dysfunction(self, bh_core: BHCore):
        """Search for mitochondrial dysfunction interventions."""
        request = api.models.SearchRequest(
            query="mitochondrial dysfunction chronic fatigue CoQ10 PQQ NAD supplementation",
            limit=5,
            year_from=2019,
        )

        response = await bh_core.search_service.search(request)

        assert response.total_found > 0, "Should find papers on mitochondrial health"

        # Check relevance
        all_text = " ".join(
            f"{r.title} {r.abstract or ''}" for r in response.results
        ).lower()

        relevant_terms = ["mitochondr", "coq10", "nad", "energy", "fatigue", "atp"]
        found_relevant = any(term in all_text for term in relevant_terms)
        assert found_relevant, "Results should be relevant to mitochondrial health"

    @pytest.mark.asyncio
    async def test_search_autoimmune_interventions(self, bh_core: BHCore):
        """Search for autoimmune protocol evidence."""
        request = api.models.SearchRequest(
            query="autoimmune protocol elimination diet rheumatoid arthritis inflammation",
            limit=5,
            year_from=2018,
        )

        response = await bh_core.search_service.search(request)

        # Verify we get results with proper scoring
        if response.results:
            # Results should be sorted by combined score (descending)
            scores = [r.combined_score for r in response.results]
            assert scores == sorted(scores, reverse=True), "Results should be sorted by score"

    @pytest.mark.asyncio
    async def test_search_hpa_axis_dysfunction(self, bh_core: BHCore):
        """Search for HPA axis related research."""
        results = await bh_core.search_service.quick_search(
            query="HPA axis dysregulation cortisol adrenal insufficiency",
            limit=5,
            year_from=2020,
        )

        assert len(results) > 0, "Should find HPA axis research"

        # All results should have basic metadata
        for result in results:
            assert result.title
            assert result.source == "qdrant"

    @pytest.mark.asyncio
    async def test_search_with_strict_filters(self, bh_core: BHCore):
        """Search with strict filtering should still return quality results."""
        request = api.models.SearchRequest(
            query="omega-3 fatty acids inflammation cardiovascular",
            limit=5,
            year_from=2022,
            min_citations=20,
            lexical_min=0.1,
        )

        response = await bh_core.search_service.search(request)

        # With strict filters, may have fewer results but should be high quality
        for result in response.results:
            if result.year:
                assert result.year >= 2022
            if result.citation_count:
                assert result.citation_count >= 20
            # Lexical score should meet threshold
            assert result.lexical_score >= 0.1

    @pytest.mark.asyncio
    async def test_client_handles_empty_results_gracefully(
        self, bh_core: BHCore
    ):
        """Client should handle queries with no results gracefully."""
        # Very specific query unlikely to have exact matches
        request = api.models.SearchRequest(
            query="xyzzy12345 nonexistent compound fake disease",
            limit=5,
            lexical_min=0.9,  # Very high threshold
        )

        response = await bh_core.search_service.search(request)

        # Should return empty but valid response
        assert response.query == request.query
        assert response.total_found == 0
        assert len(response.results) == 0
        assert response.evidence_quality == "limited"


@pytest.mark.integration
class TestBHCoreConfiguration:
    """Test configuration handling."""

    @pytest.mark.asyncio
    async def test_custom_config(self):
        """Client should accept custom configuration."""
        config = BHCoreConfig(
            xai_model="grok-4",
            xai_fast_model="grok-3-mini",
            default_limit=3,
        )

        async with BHCore(config=config) as client:
            # Should use custom config
            assert client.config.default_limit == 3
            assert client.config.xai_model == "grok-4"

    @pytest.mark.asyncio
    async def test_environment_config_loading(self):
        """Config should load from environment variables."""
        config = BHCoreConfig()

        # Should have loaded API key from environment
        assert config.xai_api_key is not None, (
            "XAI_API_KEY should be set in environment"
        )
