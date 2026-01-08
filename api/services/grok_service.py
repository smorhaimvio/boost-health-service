"""Grok service for tool-calling workflows.

This service provides Grok-specific tool calling functionality for clients.
Note: Most clients should handle tool calling on their side for better control.
"""

from typing import AsyncGenerator

from xai_sdk.aio.client import Client as XAISDKClient

from api.core.config import Settings
from api.models import GrokToolCallRequest, GrokToolCallResponse, SearchRequest
from api.services.search_service import SearchService


class GrokService:
    """Service for Grok LLM tool-calling workflows."""

    def __init__(self, config: Settings, search_service: SearchService):
        """
        Initialize Grok service.

        Args:
            config: Service configuration
            search_service: Search service for tool execution
        """
        self.config = config
        self.search_service = search_service
        
        # Initialize Grok client if API key is available
        if config.llm_api_key:
            self._client = XAISDKClient(
                api_key=config.llm_api_key,
                timeout=config.llm_timeout_seconds,
            )
        else:
            self._client = None

    async def stream_with_tools(
        self,
        request: GrokToolCallRequest,
    ) -> AsyncGenerator[GrokToolCallResponse, None]:
        """
        Stream Grok responses with automatic tool calling.

        Note: This endpoint is provided for convenience but most clients
        should handle tool calling on their side for better control.

        Args:
            request: Grok tool call request

        Yields:
            Response chunks
        """
        if not self._client:
            raise RuntimeError("Grok client not initialized - LLM_API_KEY required")

        # Placeholder implementation
        yield GrokToolCallResponse(
            chunk_type="text",
            content="Tool calling should be handled client-side for better control.",
        )
        yield GrokToolCallResponse(
            chunk_type="done",
        )

