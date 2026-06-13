"""
Retriever Module

Responsibilities:
-----------------
1. Retrieve semantically relevant chunks
2. Support metadata filtering
3. Perform hybrid retrieval
4. Prepare chunks for reranking
5. Return structured retrieval results

WHY RETRIEVAL IS IMPORTANT:
---------------------------
Retriever decides WHAT context
the LLM receives.

Bad retrieval:
---------------
- hallucinations
- irrelevant answers
- noisy context

Good retrieval:
----------------
- grounded answers
- accurate citations
- high semantic relevance

This retriever supports:
------------------------
- vector search
- BM25 keyword search
- hybrid retrieval
- reranking pipelines
"""

from typing import List, Optional

from langchain_core.documents import Document

from app.rag.vectordb import (
    search_chunks
)

from app.rag.bm25 import (
    bm25_search
)

from app.rag.hybrid_search import (
    combine_scores
)

from app.config.settings import (
    TOP_K
)


# =========================================================
# RETRIEVE RELEVANT CHUNKS
# =========================================================

def retrieve_relevant_chunks(
    question: str,
    user_id: int,
    top_k: int = TOP_K,
    document_id: Optional[str] = None
) -> List[Document]:
    """
    Retrieve relevant chunks using:
    - vector search
    - BM25 keyword scoring
    - hybrid score fusion

    PARAMETERS:
    -----------
    question:
        User query

    top_k:
        Number of chunks to retrieve

    document_id:
        Optional metadata filtering

    RETURNS:
    --------
    Hybrid-ranked chunks
    """

    # =====================================================
    # STEP 1 — VECTOR SEARCH
    # =====================================================

    results = search_chunks(

        query=question,

        user_id=user_id,

        top_k=top_k,

        document_id=document_id
    )

    # =====================================================
    # STEP 2 — EXTRACT RESULTS
    # =====================================================

    retrieved_chunks = []

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    ids = results.get(
        "ids",
        [[]]
    )[0]

    # =====================================================
    # EMPTY CHECK
    # =====================================================

    if len(documents) == 0:

        return []

    # =====================================================
    # STEP 3 — FORMAT CHUNKS
    # =====================================================

    for doc, metadata, distance, chunk_id in zip(

        documents,

        metadatas,

        distances,

        ids
    ):

        retrieved_chunks.append(

            Document(

                page_content=doc,

                metadata={

                    **metadata,

                    # Unique chunk identifier
                    "chunk_id": chunk_id,

                    # Vector similarity score
                    #
                    # Smaller distance = better match
                    "score": 1 - distance
                }
            )
        )

    # =====================================================
    # STEP 4 — BM25 KEYWORD SCORING
    # =====================================================

    retrieved_chunks = bm25_search(

        query=question,

        chunks=retrieved_chunks
    )

    # =====================================================
    # STEP 5 — HYBRID SCORE FUSION
    # =====================================================

    retrieved_chunks = combine_scores(
        retrieved_chunks
    )

    # =====================================================
    # FINAL HYBRID RANKED CHUNKS
    # =====================================================

    return retrieved_chunks
