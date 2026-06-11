"""
Chat Service

Responsibilities:
-----------------
1. Orchestrate RAG pipeline
2. Retrieve relevant chunks
3. Apply reranking
4. Build grounded prompts
5. Generate LLM responses
6. Return source citations

WHY THIS SERVICE IS IMPORTANT:
------------------------------
This is the core orchestration layer
of the chatbot system.

Pipeline:
---------
Question
    ↓
Retriever
    ↓
Reranker
    ↓
Prompt Builder
    ↓
LLM
    ↓
Grounded Response
"""

from typing import Dict, Optional

#from torch import chunk

from app.rag.retriever import (
    retrieve_relevant_chunks
)

from app.rag.reranker import (
    rerank
)

from app.rag.prompt_builder import (
    build_prompt
)

from app.rag.llm_service import (
    generate_answer
)

from app.config.settings import (
    RERANK_TOP_K
)


# =========================================================
# CHAT WITH DOCUMENTS
# =========================================================

def chat_with_documents(
    question: str,
    document_id: Optional[str] = None
) -> Dict:
    """
    Execute complete RAG pipeline.

    PARAMETERS:
    -----------
    question:
        User query

    document_id:
        Optional document filter

    RETURNS:
    --------
    Generated answer + sources
    """

    # =====================================================
    # STEP 1 — RETRIEVE CHUNKS
    # =====================================================

    retrieved_chunks = retrieve_relevant_chunks(

        question=question,

        top_k=RERANK_TOP_K,

        document_id=document_id
    )

    # =====================================================
    # STEP 2 — RERANK CHUNKS
    # =====================================================

    reranked_chunks = rerank(

        question=question,

        chunks=retrieved_chunks
    )

    # Keep best chunks after reranking
    final_chunks = reranked_chunks[:5]

    # =====================================================
    # STEP 3 — BUILD PROMPT
    # =====================================================

    prompt = build_prompt(

        question=question,

        retrieved_chunks=final_chunks
    )

    # =====================================================
    # STEP 4 — GENERATE ANSWER
    # =====================================================

    answer = generate_answer(
        prompt
    )

    # =====================================================
    # STEP 5 — BUILD SOURCES
    # =====================================================

    sources = []

    for chunk in final_chunks:

        metadata = chunk.metadata

        sources.append({

            "page": metadata.get("page"),

            "chunk_id": metadata.get(
                "chunk_id"
            ),

            "document_id": metadata.get(
                "document_id"
            )
        })

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "question": question,

        "answer": answer,

        "sources": sources
    }