"""Integration tests for intent extraction service.

These tests verify intent extraction using real Grok API calls.
Clinical queries should produce appropriate intent classifications for search optimization.
"""

import pytest

from api.core.dependencies import BHCore


@pytest.mark.integration
class TestIntentExtraction:
    """Test intent extraction with real Grok API."""

    @pytest.mark.asyncio
    async def test_extract_intent_task_type(self, bh_core: BHCore):
        """Intent should correctly identify task type."""
        query = "What is the optimal protocol for treating insulin resistance with berberine?"

        intent = await bh_core.search_service.extract_intent(query)

        assert "task_type" in intent
        assert intent["task_type"] in [
            "clinical_summary",
            "mechanism_explanation",
            "protocol",
            "differential_dx",
            "research_review",
            "general_question",
        ]

    @pytest.mark.asyncio
    async def test_extract_intent_entities(self, bh_core: BHCore):
        """Intent should extract relevant medical entities."""
        query = (
            "Explain the mechanism of how CoQ10 and NAD+ supplementation "
            "improve mitochondrial function in chronic fatigue syndrome"
        )

        intent = await bh_core.search_service.extract_intent(query)

        assert "entities" in intent
        assert isinstance(intent["entities"], list)

        # Should extract key entities
        entities_lower = [e.lower() for e in intent["entities"]]
        found_relevant = any(
            term in " ".join(entities_lower)
            for term in ["coq10", "nad", "mitochondr", "fatigue"]
        )
        assert found_relevant, f"Should extract relevant entities, got: {intent['entities']}"

    @pytest.mark.asyncio
    async def test_extract_intent_clinical_context(self, bh_core: BHCore):
        """Intent should identify clinical context category."""
        query = "How does the gut microbiome affect metabolic health and insulin sensitivity?"

        intent = await bh_core.search_service.extract_intent(query)

        assert "clinical_context" in intent
        assert intent["clinical_context"] in [
            "metabolic_health",
            "cardiovascular",
            "neurological",
            "immune",
            "longevity",
            "general",
        ]

    @pytest.mark.asyncio
    async def test_extract_intent_mechanism_query(self, bh_core: BHCore):
        """Mechanism explanation query should be identified correctly."""
        query = "What is the pathway by which berberine activates AMPK and improves glucose uptake?"

        intent = await bh_core.search_service.extract_intent(query)

        # Should identify as mechanism explanation
        assert intent.get("task_type") in [
            "mechanism_explanation",
            "research_review",
            "general_question",
        ]

    @pytest.mark.asyncio
    async def test_extract_intent_handles_long_query(self, bh_core: BHCore):
        """Long clinical case should still produce valid intent."""
        query = """
        55-year-old female presenting with chronic fatigue, brain fog, joint pain,
        and post-exertional malaise for 3 years following documented Lyme disease
        treated with 4 weeks of doxycycline. Current labs show elevated inflammatory
        markers (CRP 4.2, ESR 28), positive ANA 1:80, and low vitamin D at 22 ng/mL.
        She has tried multiple interventions including low-dose naltrexone, IV vitamins,
        and elimination diet with minimal improvement. What evidence-based treatment
        options should be considered for post-treatment Lyme disease syndrome?
        """

        intent = await bh_core.search_service.extract_intent(query)

        # Should still produce valid output
        assert intent.get("task_type"), "Should identify task type"
        assert "entities" in intent, "Should have entities list"

    @pytest.mark.asyncio
    async def test_extract_intent_research_review_query(self, bh_core: BHCore):
        """Research review query should extract appropriate intent."""
        query = (
            "What does the latest research say about the effectiveness of "
            "the autoimmune protocol diet for managing Hashimoto's thyroiditis?"
        )

        intent = await bh_core.search_service.extract_intent(query)

        # Should be research-focused
        assert intent.get("task_type") in [
            "research_review",
            "clinical_summary",
            "general_question",
        ]

        # Should identify immune context
        assert intent.get("clinical_context") in ["immune", "general"]

    @pytest.mark.asyncio
    async def test_extract_intent_lyme_disease_query(self, bh_core: BHCore):
        """Post-treatment Lyme disease query should extract relevant intent."""
        query = (
            "What are the treatment options for post-treatment Lyme disease "
            "syndrome in patients who have completed antibiotic therapy?"
        )

        intent = await bh_core.search_service.extract_intent(query)

        # Should have valid task type
        assert intent.get("task_type") in [
            "protocol",
            "clinical_summary",
            "general_question",
        ]

        # Should extract Lyme-related entities
        entities_lower = [e.lower() for e in intent.get("entities", [])]
        found_lyme = any(
            term in " ".join(entities_lower)
            for term in ["lyme", "borrelia", "ptlds", "treatment"]
        )
        assert found_lyme, f"Should extract Lyme-related entities, got: {intent['entities']}"
