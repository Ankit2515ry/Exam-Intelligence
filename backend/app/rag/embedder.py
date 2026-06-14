"""
Embedding Module

Responsibilities:
-----------------
1. Convert text into dense vectors
2. Support single embedding generation
3. Support batch embedding generation
4. Normalize embeddings for similarity search

WHY EMBEDDINGS MATTER:
----------------------
Embeddings transform text into numerical vectors
that capture semantic meaning.

Example:
--------
"database normalization"
and
"removing redundancy"

will have similar embeddings even if wording differs.

These vectors power:
- semantic retrieval
- vector search
- reranking pipelines
- similarity matching
"""

from typing import List

# from sentence_transformers import (
#     SentenceTransformer
# )

from app.config.settings import (
    EMBEDDING_MODEL
)


# =========================================================
# LOAD EMBEDDING MODEL
# =========================================================

"""
Model loaded ONCE globally.

WHY?
----
Loading transformer models repeatedly is expensive.

Global loading:
---------------
✅ faster inference
✅ lower memory overhead
✅ production-friendly
"""

# embedding_model = SentenceTransformer(
#     "all-MiniLM-L6-v2"
# )

_model = None

def get_embedding_model():
    global _model

    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    return _model

# =========================================================
# SINGLE TEXT EMBEDDING
# =========================================================

def generate_embedding(
    text: str
) -> List[float]:
    """
    Generate embedding for a single text.

    PARAMETERS:
    -----------
    text:
        Input text

    RETURNS:
    --------
    Dense vector embedding
    """

    # Prevent embedding empty text
    if not text.strip():
        return []

    embedding = embedding_model.encode(

        text,

        normalize_embeddings=True
    )

    return embedding.tolist()


# =========================================================
# BATCH EMBEDDING
# =========================================================

def generate_embeddings(
    texts: List[str]
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts.

    WHY BATCH EMBEDDING?
    --------------------
    Batch processing is MUCH faster than:
    loop -> encode -> loop -> encode

    Used during:
    ------------
    document ingestion
    chunk embedding
    bulk indexing
    """

    # Remove empty texts
    valid_texts = [

        text for text in texts

        if text.strip()
    ]

    if not valid_texts:
        return []

    embeddings = embedding_model.encode(

        valid_texts,

        normalize_embeddings=True
    )

    return embeddings.tolist()