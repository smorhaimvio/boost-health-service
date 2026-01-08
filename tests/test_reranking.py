"""Tests for reranking service and lexical filtering.

These tests verify the hybrid scoring algorithm works correctly,
combining vector similarity, lexical overlap, and metadata bonuses.
"""

import pytest

from api.models import SearchResult
from api.services.reranking_service import RerankingService
from api.vector_db.lexical_filter import compute_lexical_score, STOPWORDS


class TestLexicalScoring:
    """Test lexical overlap scoring for search relevance."""

    def test_exact_match_high_score(self):
        """Query terms appearing in title/abstract should score high."""
        query = "berberine insulin resistance"
        title = "Berberine improves insulin resistance in type 2 diabetes"
        abstract = "This study examines how berberine affects insulin sensitivity."

        score = compute_lexical_score(query, title, abstract)

        # Should have high coverage since key terms match
        assert score > 0.5, f"Exact match should score high, got {score}"

    def test_no_match_low_score(self):
        """Completely unrelated content should score near zero."""
        query = "berberine insulin resistance"
        title = "Ocean acidification effects on coral reefs"
        abstract = "Marine ecosystems are affected by climate change."

        score = compute_lexical_score(query, title, abstract)

        assert score < 0.1, f"Unrelated content should score low, got {score}"

    def test_partial_match_medium_score(self):
        """Partial term overlap should give intermediate score."""
        query = "MTHFR methylation folate supplementation"
        title = "Folate metabolism in pregnancy"
        abstract = "Supplementation of folic acid is recommended."

        score = compute_lexical_score(query, title, abstract)

        # Some overlap (folate, supplementation) but not all terms
        assert 0.1 < score < 0.8, f"Partial match should score medium, got {score}"

    def test_stopwords_excluded(self):
        """Common words should not inflate scores."""
        query = "the effects of insulin on glucose"
        title = "Insulin and glucose metabolism"
        abstract = None

        score = compute_lexical_score(query, title, abstract)

        # 'the', 'of', 'on' should be excluded
        assert "the" in STOPWORDS
        assert "of" in STOPWORDS
        assert "on" in STOPWORDS

    def test_clinical_term_matching(self):
        """Clinical/medical terms should be matched properly."""
        query = "post-treatment Lyme disease syndrome PTLDS"
        title = "Post-treatment Lyme Disease Syndrome: Clinical Outcomes"
        abstract = "Patients with PTLDS experience persistent symptoms."

        score = compute_lexical_score(query, title, abstract)

        assert score > 0.3, "Clinical terms should match well"


class TestRerankingService:
    """Test the reranking algorithm combining multiple signals."""

    @pytest.fixture
    def reranker(self) -> RerankingService:
        return RerankingService()

    @pytest.fixture
    def sample_results(self) -> list[SearchResult]:
        """Create sample search results for testing."""
        return [
            SearchResult(
                paper_id="paper1",
                title="Berberine for insulin resistance: a meta-analysis",
                abstract="Berberine significantly improves insulin sensitivity.",
                year=2023,
                citation_count=100,
                vector_score=0.85,
                publication_type="Meta-Analysis",
            ),
            SearchResult(
                paper_id="paper2",
                title="Glucose metabolism in elderly patients",
                abstract="Age-related changes in glucose handling.",
                year=2019,
                citation_count=25,
                vector_score=0.80,
                publication_type="Review",
            ),
            SearchResult(
                paper_id="paper3",
                title="Insulin receptor signaling pathways",
                abstract="Molecular mechanisms of insulin action.",
                year=2021,
                citation_count=8,
                vector_score=0.90,
                publication_type="Original Research",
            ),
        ]

    def test_reranking_boosts_recent_papers(
        self, reranker: RerankingService, sample_results: list[SearchResult]
    ):
        """Papers from 2022+ should get recency bonus."""
        query = "berberine insulin resistance"

        # Use lexical_min=0.0 to prevent filtering so we can compare all papers
        reranked = reranker.rerank(query, sample_results, lexical_min=0.0)

        # Paper1 (2023) should get recency bonus
        paper1 = next(r for r in reranked if r.paper_id == "paper1")
        paper2 = next(r for r in reranked if r.paper_id == "paper2")

        # 2023 paper should score higher than 2019 paper (after metadata bonus)
        assert paper1.combined_score > paper2.combined_score

    def test_reranking_boosts_high_citations(
        self, reranker: RerankingService
    ):
        """Papers with 50+ citations should get citation bonus."""
        # Create results with equal vector scores to isolate citation effect
        results = [
            SearchResult(
                paper_id="high_citations",
                title="Insulin resistance mechanisms",
                abstract="Molecular pathways of insulin signaling.",
                year=2021,
                citation_count=100,
                vector_score=0.85,
            ),
            SearchResult(
                paper_id="low_citations",
                title="Insulin receptor studies",
                abstract="Investigation of insulin binding.",
                year=2021,
                citation_count=5,
                vector_score=0.85,
            ),
        ]

        query = "insulin resistance mechanisms"
        reranked = reranker.rerank(query, results, lexical_min=0.0)

        # High citation paper should get citation bonus
        high_cite = next(r for r in reranked if r.paper_id == "high_citations")
        low_cite = next(r for r in reranked if r.paper_id == "low_citations")

        # With equal vector scores, high citation paper should score better
        assert high_cite.combined_score > low_cite.combined_score

    def test_reranking_filters_by_lexical_min(
        self, reranker: RerankingService
    ):
        """Results below lexical minimum should be filtered out."""
        results = [
            SearchResult(
                paper_id="relevant",
                title="Mitochondrial dysfunction in chronic fatigue",
                abstract="CoQ10 supplementation improves energy.",
                vector_score=0.8,
            ),
            SearchResult(
                paper_id="irrelevant",
                title="Ocean currents and climate patterns",
                abstract="Global circulation models predict changes.",
                vector_score=0.75,
            ),
        ]

        query = "mitochondrial dysfunction chronic fatigue CoQ10"
        reranked = reranker.rerank(query, results, lexical_min=0.1)

        # Irrelevant paper should be filtered out
        paper_ids = [r.paper_id for r in reranked]
        assert "relevant" in paper_ids
        assert "irrelevant" not in paper_ids

    def test_evidence_quality_strong_for_reviews(
        self, reranker: RerankingService
    ):
        """Reviews and meta-analyses should be marked as strong evidence."""
        results = [
            SearchResult(
                paper_id="meta",
                title="Systematic review of gut microbiome interventions",
                publication_type="Meta-Analysis",
                vector_score=0.8,
            ),
        ]

        quality = reranker.assess_evidence_quality(results)
        assert quality == "strong"

    def test_evidence_quality_limited_for_few_primary_studies(
        self, reranker: RerankingService
    ):
        """Few primary studies should be marked as limited evidence."""
        results = [
            SearchResult(
                paper_id="study1",
                title="Pilot study of NAD+ supplementation",
                publication_type="Clinical Trial",
                vector_score=0.8,
            ),
        ]

        quality = reranker.assess_evidence_quality(results)
        assert quality == "limited"

    def test_combined_score_calculation(
        self, reranker: RerankingService
    ):
        """Verify combined score includes all components."""
        results = [
            SearchResult(
                paper_id="test",
                title="Autoimmune protocol diet for rheumatoid arthritis",
                abstract="AIP diet reduces inflammation markers.",
                year=2023,
                citation_count=60,
                vector_score=0.75,
            ),
        ]

        query = "autoimmune protocol diet rheumatoid arthritis"
        reranked = reranker.rerank(query, results, lexical_min=0.0)

        result = reranked[0]

        # Combined should be higher than vector alone due to bonuses
        assert result.combined_score > result.vector_score
        assert result.lexical_score > 0
