"""MedCPT encoder wrapper for biomedical text encoding.

Uses separate encoders for articles and queries.
"""

from typing import List

import numpy as np
import torch
from sentence_transformers import SentenceTransformer, models


class MedCPTEncoder:
    """
    Wrapper for MedCPT encoders.

    MedCPT uses separate models:
    - Article Encoder: For encoding article abstracts
    - Query Encoder: For encoding user queries

    This design optimizes for asymmetric retrieval tasks.
    """

    # MedCPT model identifiers on HuggingFace
    ARTICLE_ENCODER = "ncbi/MedCPT-Article-Encoder"
    QUERY_ENCODER = "ncbi/MedCPT-Query-Encoder"

    def __init__(self, device: str | None = None):
        """
        Initialize MedCPT encoders.

        Args:
            device: Device to run models on ('cuda', 'mps', or 'cpu')
        """
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = device
        print(f"Using device: {self.device}")

        # Helper to load with CLS pooling (required for MedCPT)
        def load_model_with_cls_pooling(model_name):
            print(f"Loading {model_name} with [CLS] pooling...")
            word_embedding_model = models.Transformer(model_name)
            pooling_model = models.Pooling(
                word_embedding_model.get_word_embedding_dimension(),
                pooling_mode="cls",  # Explicitly force CLS pooling
            )
            return SentenceTransformer(
                modules=[word_embedding_model, pooling_model], device=self.device
            )

        self.article_encoder = load_model_with_cls_pooling(self.ARTICLE_ENCODER)
        self.query_encoder = load_model_with_cls_pooling(self.QUERY_ENCODER)

        print("MedCPT encoders loaded successfully!")

        # Get embedding dimension
        self.embedding_dim = self.article_encoder.get_sentence_embedding_dimension()
        print(f"Embedding dimension: {self.embedding_dim}")

    async def load(self) -> None:
        """Async load method for compatibility (encoders are already loaded in __init__)."""
        pass

    def encode_articles(
        self,
        texts: "str | List[str]",
        batch_size: int = 32,
        show_progress: bool = True,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode article texts using the Article Encoder.

        Args:
            texts: Single text or list of texts to encode
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length (for cosine similarity)

        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.article_encoder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )

        return embeddings

    def encode_queries(
        self,
        queries: "str | List[str]",
        batch_size: int = 32,
        show_progress: bool = True,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode query texts using the Query Encoder.

        Args:
            queries: Single query or list of queries to encode
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            normalize: Normalize embeddings to unit length (for cosine similarity)

        Returns:
            Numpy array of embeddings
        """
        if isinstance(queries, str):
            queries = [queries]

        embeddings = self.query_encoder.encode(
            queries,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )

        return embeddings

    def prepare_article_text(self, title: str, abstract: str) -> str:
        """
        Prepare article text for encoding.
        Combines title and abstract.

        Args:
            title: Paper title
            abstract: Paper abstract

        Returns:
            Combined text for encoding
        """
        # Combine title and abstract with clear separation
        text = f"{title}\n\n{abstract}"
        return text

