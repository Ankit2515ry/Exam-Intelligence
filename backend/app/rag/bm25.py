"""
BM25 Keyword Search
"""

from rank_bm25 import BM25Okapi


def bm25_search(
    query,
    chunks,
    top_k=5
):

    # =====================================================
    # EMPTY CHECK
    # =====================================================

    if not chunks:

        return []

    # =====================================================
    # TOKENIZE CHUNKS
    # =====================================================

    tokenized_chunks = [

        chunk.page_content.split()

        for chunk in chunks
    ]

    # =====================================================
    # CREATE BM25 INDEX
    # =====================================================

    bm25 = BM25Okapi(
        tokenized_chunks
    )

    # =====================================================
    # TOKENIZE QUERY
    # =====================================================

    query_tokens = query.split()

    # =====================================================
    # BM25 SCORES
    # =====================================================

    scores = bm25.get_scores(
        query_tokens
    )

    # =====================================================
    # ATTACH BM25 SCORES
    # =====================================================

    for chunk, score in zip(chunks, scores):

        chunk.metadata["bm25_score"] = float(score)

    # =====================================================
    # SORT BY BM25 SCORE
    # =====================================================

    ranked_chunks = sorted(

        chunks,

        key=lambda x: x.metadata["bm25_score"],

        reverse=True
    )

    # =====================================================
    # RETURN TOP-K
    # =====================================================

    return ranked_chunks[:top_k]
