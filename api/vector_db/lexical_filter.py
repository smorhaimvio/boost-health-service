"""Lexical filtering and scoring for search results."""

# Stopwords for lexical scoring
STOPWORDS = {
    # Common English function words
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "without",
    # Generic research terms
    "study",
    "studies",
    "trial",
    "trials",
    "randomized",
    "randomised",
    "controlled",
    "double",
    "blind",
    "placebo",
    "effect",
    "effects",
    "treatment",
    "therapy",
    "patient",
    "patients",
    "women",
    "men",
    "woman",
    "man",
    "human",
    "humans",
    "subjects",
    "subject",
    "participants",
    "participant",
    "group",
    "groups",
    "outcome",
    "outcomes",
    "risk",
    "risks",
    "association",
    "associated",
    "impact",
    "clinical",
    "cohort",
    "review",
    "analysis",
    "analyzed",
    "evaluated",
    "compared",
    "result",
    "results",
    "data",
    "method",
    "methods",
    "research",
    "sample",
    "population",
    "design",
    "findings",
    "conclusion",
    "background",
    "objective",
    "intervention",
    "interventions",
    "measure",
    "measured",
    "assessment",
}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words, stripping punctuation."""
    text = text.lower()
    for ch in ",.;:()[]{}\"'!?/-":
        text = text.replace(ch, " ")
    tokens = [t for t in text.split() if t]
    return tokens


def compute_lexical_score(query: str, title: str, abstract: str | None) -> float:
    """
    Compute lexical overlap score between query and document.

    Args:
        query: Search query
        title: Document title
        abstract: Document abstract (optional)

    Returns:
        Lexical score (0.0 to 1.0+)
    """
    query_tokens = _tokenize(query)
    doc_text = title
    if abstract:
        doc_text += " " + abstract
    doc_tokens = _tokenize(doc_text)

    # Filter out stopwords
    query_content = [t for t in query_tokens if t not in STOPWORDS]
    doc_content = [t for t in doc_tokens if t not in STOPWORDS]

    if not query_content or not doc_content:
        return 0.0

    query_set = set(query_content)
    doc_set = set(doc_content)

    overlap = query_set & doc_set
    overlap_count = len(overlap)
    query_content_len = len(query_set)

    if query_content_len == 0:
        return 0.0

    coverage = overlap_count / query_content_len
    return coverage + 0.1 * overlap_count

