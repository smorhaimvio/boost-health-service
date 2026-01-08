"""Pytest fixtures for BH Service tests.

These fixtures provide real, initialized core for integration testing.
No mocking - all tests hit real services (Qdrant, Grok).
"""

import pytest
import pytest_asyncio

from api.core.dependencies import BHCore
from api.core.config import Settings


@pytest.fixture(scope="session")
def bh_config() -> Settings:
    """Load BH Service configuration from environment."""
    return Settings()


@pytest_asyncio.fixture
async def bh_core(bh_config: Settings) -> BHCore:
    """Provide an initialized BH Client for testing.

    This client connects to real Qdrant and Grok services.
    Tests using this fixture are integration tests.
    """
    client = BHCore(config=bh_config)
    await client.initialize()
    yield client
    await client.close()


@pytest.fixture
def clinical_queries() -> dict[str, str]:
    """Clinical query examples for testing.

    These are real functional medicine / integrative health queries
    that would be used by clinicians.
    """
    return {
        "post_treatment_lyme": (
            "post-treatment Lyme disease syndrome persistent symptoms treatment options"
        ),
        "mold_toxicity": (
            "mycotoxin exposure chronic inflammatory response syndrome CIRS treatment"
        ),
        "metabolic_dysfunction": (
            "insulin resistance metabolic syndrome berberine metformin comparison"
        ),
        "gut_microbiome": (
            "gut microbiome dysbiosis functional medicine interventions probiotics"
        ),
        "mitochondrial_dysfunction": (
            "mitochondrial dysfunction chronic fatigue CoQ10 NAD+ supplementation"
        ),
        "autoimmune_protocol": (
            "autoimmune protocol diet AIP rheumatoid arthritis clinical trials"
        ),
        "hpa_axis": (
            "HPA axis dysregulation adrenal fatigue cortisol testing treatment"
        ),
        "methylation": (
            "MTHFR polymorphism methylation support folate supplementation"
        ),
    }
