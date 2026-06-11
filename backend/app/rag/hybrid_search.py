"""
Hybrid Search Score Fusion
"""

from typing import List

from langchain_core.documents import Document


# =========================================================
# COMBINE VECTOR + BM25 SCORES
# =========================================================

def combine_scores(
    chunks: List[Document]
) -> List[Document]:
    """
    Combine:
    - vector similarity score
    - BM25 keyword score

    Uses weighted fusion.
    """

    # =====================================================
    # EMPTY CHECK
    # =====================================================

    if not chunks:

        return []

    # =====================================================
    # EXTRACT SCORES
    # =====================================================

    vector_scores = [

        chunk.metadata.get("score", 0.0)

        for chunk in chunks
    ]

    bm25_scores = [

        chunk.metadata.get("bm25_score", 0.0)

        for chunk in chunks
    ]

    # =====================================================
    # SAFE NORMALIZATION
    # =====================================================

    max_vector = max(vector_scores) if vector_scores else 1.0

    max_bm25 = max(bm25_scores) if bm25_scores else 1.0

    # Prevent division by zero

    if max_vector == 0:
        max_vector = 1.0

    if max_bm25 == 0:
        max_bm25 = 1.0

    # =====================================================
    # COMPUTE HYBRID SCORES
    # =====================================================

    for chunk in chunks:

        vector_score = (

            chunk.metadata.get("score", 0.0)

            / max_vector
        )

        bm25_score = (

            chunk.metadata.get("bm25_score", 0.0)

            / max_bm25
        )

        # Weighted fusion

        hybrid_score = (

            0.7 * vector_score +

            0.3 * bm25_score
        )

        # Store hybrid score

        chunk.metadata["hybrid_score"] = (
            hybrid_score
        )

    # =====================================================
    # SORT BY HYBRID SCORE
    # =====================================================

    ranked_chunks = sorted(

        chunks,

        key=lambda x: (
            x.metadata["hybrid_score"]
        ),

        reverse=True
    )

    # =====================================================
    # FINAL RANKED CHUNKS
    # =====================================================

    return ranked_chunks
