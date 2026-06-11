"""
Reranker Module
"""

from typing import List

from langchain_core.documents import Document

from sentence_transformers import (
    CrossEncoder
)

from app.config.settings import (
    RERANK_MODEL
)


# =========================================================
# LOAD RERANKER MODEL
# =========================================================

reranker_model = CrossEncoder(
    RERANK_MODEL
)


# =========================================================
# RERANK CHUNKS
# =========================================================

def rerank(
    question: str,
    chunks: List[Document]
) -> List[Document]:
    """
    Rerank retrieved chunks.
    """

    # =====================================================
    # EMPTY CHECK
    # =====================================================

    if not chunks:
        return []

    # =====================================================
    # BUILD QUESTION-CHUNK PAIRS
    # =====================================================

    pairs = [

        (
            question,
            chunk.page_content
        )

        for chunk in chunks
    ]

    # =====================================================
    # COMPUTE RERANK SCORES
    # =====================================================

    scores = reranker_model.predict(
        pairs
    )

    # =====================================================
    # ATTACH SCORES
    # =====================================================

    for chunk, score in zip(
        chunks,
        scores
    ):

        chunk.metadata["rerank_score"] = (
            float(score)
        )

    # =====================================================
    # SORT BY RERANK SCORE
    # =====================================================

    chunks.sort(

        key=lambda chunk: (
            chunk.metadata["rerank_score"]
        ),

        reverse=True
    )

    return chunks
