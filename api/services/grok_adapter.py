"""Grok LLM adapter implementation."""

import json
from typing import Any, Dict

from xai_sdk.aio.client import Client as XAISDKClient

from api.services.llm_adapter import LLMAdapter


class GrokAdapter(LLMAdapter):
    """Grok implementation of LLM adapter."""

    def __init__(self, api_key: str, timeout: float = 180.0):
        """
        Initialize Grok adapter.

        Args:
            api_key: XAI API key
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self._client = XAISDKClient(api_key=api_key, timeout=timeout)

    async def complete(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """Get a completion from Grok."""
        from xai_sdk.chat import system as system_msg, user as user_msg
        
        # Create chat
        chat = self._client.chat.create(
            model=model or "grok-4-fast-non-reasoning",
            temperature=temperature,
        )
        
        # Add system prompt if provided
        if system_prompt:
            chat.append(system_msg(system_prompt))
        
        # Add messages
        for msg in messages:
            if msg["role"] == "user":
                chat.append(user_msg(msg["content"]))
            elif msg["role"] == "system":
                chat.append(system_msg(msg["content"]))
        
        # Sample response
        response = await chat.sample()
        return response.content or ""

    async def complete_json(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """Get a JSON completion from Grok."""
        # Add JSON instruction to system prompt
        json_instruction = "You must respond with valid JSON only. No markdown, no explanations."
        if system_prompt:
            full_system_prompt = f"{system_prompt}\n\n{json_instruction}"
        else:
            full_system_prompt = json_instruction

        # Get completion
        response_text = await self.complete(
            messages=messages,
            system_prompt=full_system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=500,
        )

        # Parse JSON
        # Remove markdown code blocks if present
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return json.loads(cleaned.strip())

