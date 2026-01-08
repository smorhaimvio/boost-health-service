"""Intent extraction service for understanding search query intent.

Extracts structured intent from user queries to optimize search and context.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from api.core.config import Settings
from api.services.llm_adapter import LLMAdapter


logger = logging.getLogger(__name__)


# System prompt for intent extraction (search-focused)
INTENT_EXTRACTION_PROMPT = """Extract the search intent from this medical/health query.

Output ONLY valid JSON in this exact format:
{
  "task_type": "clinical_summary | mechanism_explanation | protocol | differential_dx | research_review | general_question",
  "entities": ["key terms", "compounds", "conditions"],
  "clinical_context": "metabolic_health | cardiovascular | neurological | immune | longevity | general"
}

Be concise and specific. Extract key medical/scientific entities that would be useful for search."""


class IntentService:
    """Service for extracting search intent from user messages.

    This service analyzes user queries to understand:
    - Task type (what kind of answer they need)
    - Key entities (medical terms, compounds, conditions)
    - Clinical context (health domain)

    This intent is used to optimize search queries and result ranking.
    """

    def __init__(self, config: Settings, llm_adapter: LLMAdapter):
        """
        Initialize intent service.

        Args:
            config: Service configuration
            llm_adapter: LLM adapter for completions
        """
        self.config = config
        self._llm = llm_adapter

    async def extract_intent(
        self,
        user_message: str,
    ) -> Dict[str, Any]:
        """Extract search intent from user message using LLM.

        Args:
            user_message: The user's prompt/question

        Returns:
            Intent dictionary with task_type, entities, clinical_context

        Example:
            >>> intent = await service.extract_intent("What is berberine?")
            >>> intent['task_type']
            'general_question'
            >>> intent['entities']
            ['berberine']
        """
        try:
            # Truncate very long messages
            truncated_message = (
                user_message[:500] if len(user_message) > 500 else user_message
            )

            # Use LLM adapter for JSON completion
            intent = await self._llm.complete_json(
                messages=[{"role": "user", "content": f"User query: {truncated_message}"}],
                system_prompt=INTENT_EXTRACTION_PROMPT,
                temperature=0.3,
            )

            # Validate intent structure
            if not isinstance(intent, dict) or not intent.get("task_type"):
                return _generate_fallback_intent(user_message)

            return intent

        except Exception as e:
            logger.warning(f"Intent extraction failed: {e}")
            return _generate_fallback_intent(user_message)


def _generate_fallback_intent(message: str) -> Dict[str, Any]:
    """Generate a simple fallback intent from the message.

    Args:
        message: User message

    Returns:
        Basic intent dictionary
    """
    clean_message = re.sub(r"<[^>]+>", " ", message).lower()

    # Simple keyword detection for task type
    task_type = "general_question"
    if any(
        word in clean_message
        for word in ["explain", "mechanism", "how does", "pathway"]
    ):
        task_type = "mechanism_explanation"
    elif any(
        word in clean_message for word in ["protocol", "treatment", "intervention"]
    ):
        task_type = "protocol"
    elif any(word in clean_message for word in ["summarize", "summary", "overview"]):
        task_type = "clinical_summary"
    elif any(word in clean_message for word in ["research", "studies", "evidence"]):
        task_type = "research_review"

    # Extract potential entities
    words = re.findall(r"\b[a-z]{4,}\b", clean_message)
    entities = list(set([w for w in words if len(w) > 3]))[:5]

    # Detect clinical context
    clinical_context = "general"
    if any(
        word in clean_message
        for word in ["metabolic", "insulin", "glucose", "diabetes"]
    ):
        clinical_context = "metabolic_health"
    elif any(
        word in clean_message for word in ["heart", "cardiovascular", "blood pressure"]
    ):
        clinical_context = "cardiovascular"
    elif any(word in clean_message for word in ["brain", "cognitive", "neuro"]):
        clinical_context = "neurological"
    elif any(word in clean_message for word in ["aging", "longevity", "lifespan"]):
        clinical_context = "longevity"

    return {
        "task_type": task_type,
        "entities": entities,
        "clinical_context": clinical_context,
    }
