"""BH Client request/response models."""

from pydantic import BaseModel, Field
from typing import Literal


class SearchRequest(BaseModel):
    """Request for BH Client search."""

    query: str = Field(..., description="Search query")
    limit: int = Field(5, description="Maximum results to return")
    year_from: int | None = Field(None, description="Filter by publication year (minimum)")
    year_to: int | None = Field(None, description="Filter by publication year (maximum)")
    min_citations: int | None = Field(None, description="Minimum citation count")
    lexical_min: float = Field(0.05, description="Minimum lexical score threshold")
    publication_types: list[str] | None = Field(None, description="Filter by publication types")
    use_reranking: bool = Field(True, description="Apply hybrid reranking")
    use_lexical_filter: bool = Field(True, description="Apply lexical filtering")


class SearchResult(BaseModel):
    """A single search result."""

    paper_id: str
    title: str
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    citation_count: int | None = None
    publication_type: str | None = None
    doi: str | None = None
    url: str | None = None

    # Scoring
    vector_score: float = 0.0
    lexical_score: float = 0.0
    combined_score: float = 0.0

    # Metadata
    source: str = "qdrant"
    evidence_quality: int = 0  # Quality score 0-5


class SearchResponse(BaseModel):
    """Response from BH Client search."""

    query: str
    results: list[SearchResult]
    total_found: int
    evidence_quality: int  # Quality score 0-5
    search_time_ms: float
    metadata: dict = Field(default_factory=dict)


class StreamingSearchEvent(BaseModel):
    """Event for streaming search responses."""

    event_type: Literal["result", "status", "error", "done"]
    data: SearchResult | dict | str | None = None

class GrokToolCallRequest(BaseModel):
    """Request for Grok-driven tool calling search."""

    messages: list[dict]
    system_prompt: str | None = None
    model: str = "grok-4"
    tools: list[dict] | None = None
    stream: bool = True
    max_tool_calls: int = 10


class GrokToolCallResponse(BaseModel):
    """Response chunk from Grok tool calling."""

    chunk_type: Literal["text", "tool_call", "tool_result", "done"]
    content: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: list[SearchResult] | None = None
    usage: dict | None = None


