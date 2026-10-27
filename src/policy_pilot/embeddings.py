"""Turn text into vectors with an open-source multilingual model that runs locally."""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from policy_pilot import config


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(config.EMBEDDING_MODEL)


def embed_passages(texts: list[str]) -> np.ndarray:
    return _model().encode(texts, normalize_embeddings=True, show_progress_bar=True)


def embed_query(question: str) -> np.ndarray:
    return _model().encode(question, normalize_embeddings=True)