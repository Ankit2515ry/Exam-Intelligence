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

import logging
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
from app.observability.performance import stage, set_count

logger = logging.getLogger(__name__)

NO_CONTEXT_ANSWER = (
    "I could not find relevant information in the uploaded documents."
)


# =========================================================
# CHAT WITH DOCUMENTS
# =========================================================

def chat_with_documents(
    question: str,
    user_id: int,
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

    logger.info(
        "Starting chat request user_id=%s document_id=%s",
        user_id,
        document_id or "all",
    )

    # =====================================================
    # STEP 1 — RETRIEVE CHUNKS
    # =====================================================

    retrieved_chunks = retrieve_relevant_chunks(

        question=question,

        user_id=user_id,

        top_k=RERANK_TOP_K,

        document_id=document_id
    )
    logger.info(
        "Retrieved chunks for chat user_id=%s count=%s",
        user_id,
        len(retrieved_chunks),
    )

    if not retrieved_chunks:
        logger.info(
            "No relevant document context found for user_id=%s document_id=%s",
            user_id,
            document_id or "all",
        )
        return {
            "question": question,
            "answer": NO_CONTEXT_ANSWER,
            "sources": []
        }

    # =====================================================
    # STEP 2 — RERANK CHUNKS
    # =====================================================

    with stage("reranking"):
        reranked_chunks = rerank(
            question=question,
            chunks=retrieved_chunks
        )

    # Keep best chunks after reranking
    final_chunks = reranked_chunks[:5]
    set_count("final_source_chunks", len(final_chunks))
    logger.info(
        "Selected chunks for chat user_id=%s count=%s",
        user_id,
        len(final_chunks),
    )

    if not final_chunks:
        logger.info(
            "No document context remained after reranking for user_id=%s document_id=%s",
            user_id,
            document_id or "all",
        )
        return {
            "question": question,
            "answer": NO_CONTEXT_ANSWER,
            "sources": []
        }

    # =====================================================
    # STEP 3 — BUILD PROMPT
    # =====================================================

    with stage("prompt_construction"):
        prompt = build_prompt(
            question=question,
            retrieved_chunks=final_chunks
        )

    # print("\n" + "="*80)
    # print("PROMPT SENT TO LLM")
    # print("="*80)
    # print(prompt)
    # print("="*80 + "\n")

    # =====================================================
    # STEP 4 — GENERATE ANSWER
    # =====================================================

    with stage("gemini_api"):
        answer = generate_answer(prompt)
    logger.info(
        "Generated chat answer user_id=%s source_count=%s",
        user_id,
        len(final_chunks),
    )

    # answer = prompt

    # =====================================================
    # STEP 5 — BUILD SOURCES
    # =====================================================

    sources = []

    for chunk in final_chunks:

        metadata = chunk.metadata

        # sources.append({

        #     "page": metadata.get("page"),

        #     "chunk_id": metadata.get(
        #         "chunk_id"
        #     ),

        #     "document_id": metadata.get(
        #         "document_id"
        #     )
        # })

        sources.append({

            "page": metadata.get("page"),

            "chunk_id": metadata.get("chunk_id"),

            "document_id": metadata.get("document_id"),

            "content": chunk.page_content
        })

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "question": question,

        "answer": answer,

        "sources": sources
    }
