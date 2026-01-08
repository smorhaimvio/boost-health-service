"""LLM adapter interface for BH Service.

This allows BH Service to use any LLM provider without being tied to a specific one.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMAdapter(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """
        Get a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            model: Optional model override
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            The completion text
        """
        pass

    @abstractmethod
    async def complete_json(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Get a JSON completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            model: Optional model override
            temperature: Sampling temperature

        Returns:
            Parsed JSON response
        """
        pass

