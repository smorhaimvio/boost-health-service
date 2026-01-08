"""Grok service for tool-calling workflows (FM Agent compatibility).

This service exists for backward compatibility with FM Agent's expectations.
It provides Grok-specific tool calling functionality.
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

        This is a placeholder for FM Agent compatibility.
        The actual tool calling should be done in FM Agent.

        Args:
            request: Grok tool call request

        Yields:
            Response chunks
        """
        if not self._client:
            raise RuntimeError("Grok client not initialized - LLM_API_KEY required")

        # For now, just yield a message that this should be done in FM Agent
        yield GrokToolCallResponse(
            chunk_type="text",
            content="Tool calling should be handled by FM Agent, not BH Service.",
        )
        yield GrokToolCallResponse(
            chunk_type="done",
        )

