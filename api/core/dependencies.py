"""Dependency injection for BoostHealth Service."""

from __future__ import annotations
from typing import TYPE_CHECKING

from api.core.config import get_settings

if TYPE_CHECKING:
    from api.services.search_service import SearchService
    from api.services.intent_service import IntentService
    from api.services.llm_adapter import LLMAdapter
    from api.services.grok_service import GrokService


class BHCore:
    """Core BoostHealth Service components."""
    
    def __init__(self):
        """Initialize BH Core."""
        self.settings = get_settings()
        self._search_service: SearchService | None = None
        self._intent_service: IntentService | None = None
        self._llm_adapter: LLMAdapter | None = None
        self._grok_service: GrokService | None = None
    
    async def initialize(self):
        """Initialize all services."""
        # Import here to avoid circular imports
        from api.services.search_service import SearchService
        from api.services.grok_service import GrokService
        from api.services.intent_service import IntentService
        from api.services.grok_adapter import GrokAdapter
        
        # Initialize LLM adapter (for intent extraction)
        if not self.settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is required for intent extraction")
        self._llm_adapter = GrokAdapter(
            api_key=self.settings.llm_api_key,
            timeout=self.settings.llm_timeout_seconds,
        )
        
        # Initialize search service (it will init encoder and qdrant internally)
        self._search_service = SearchService(config=self.settings)
        await self._search_service.initialize()
        
        # Initialize intent service
        self._intent_service = IntentService(
            config=self.settings,
            llm_adapter=self._llm_adapter,
        )
        
        # Initialize Grok service
        self._grok_service = GrokService(
            config=self.settings,
            search_service=self._search_service,
        )
    
    async def close(self):
        """Close all connections."""
        if self._search_service:
            await self._search_service.close()
    
    @property
    def search_service(self) -> SearchService:
        """Get search service."""
        if not self._search_service:
            raise RuntimeError("BH Core not initialized")
        return self._search_service
    
    @property
    def intent_service(self) -> IntentService:
        """Get intent service."""
        if not self._intent_service:
            raise RuntimeError("BH Core not initialized")
        return self._intent_service
    
    @property
    def grok_service(self) -> GrokService:
        """Get Grok service."""
        if not self._grok_service:
            raise RuntimeError("BH Core not initialized")
        return self._grok_service


# Global instance
_bh_core: BHCore | None = None


def set_bh_core(core: BHCore):
    """Set global BH Core instance."""
    global _bh_core
    _bh_core = core


def get_bh_core() -> BHCore:
    """Get global BH Core instance."""
    if _bh_core is None:
        raise RuntimeError("BH Core not initialized")
    return _bh_core

