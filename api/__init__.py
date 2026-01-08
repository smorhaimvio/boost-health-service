"""
BoostHealth (BH) Service - Intelligence Platform for HealthTech

An intelligence platform that ingests, governs, and prioritizes regulatory,
clinical, and policy sources, then retrieves structured evidence on demand.

This implementation provides evidence search capabilities powered by:
- Vector search via Qdrant with MedCPT embeddings
- Lexical filtering for precision
- Hybrid reranking for relevance
- Intent extraction via LLM adapter

Serves as the intelligence layer for automated healthcare decisions.
"""

__version__ = "1.0.0"

