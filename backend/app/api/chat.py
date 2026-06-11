"""
Chat API Routes

Responsibilities:
-----------------
1. Receive user questions
2. Validate requests
3. Call chat orchestration service
4. Return grounded responses

IMPORTANT:
-----------
This API layer should remain THIN.

It should NOT:
---------------
- retrieve vectors
- rerank chunks
- build prompts
- call vector DB directly

All orchestration belongs inside:
services/chat_service.py
"""

from fastapi import APIRouter

from app.models.chat import (
    ChatRequest,
    ChatResponse
)

from app.services.chat_service import (
    chat_with_documents
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(

    prefix="/api",

    tags=["Chat"]
)


# =========================================================
# CHAT ENDPOINT
# =========================================================

@router.post(
    "/chat",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest
):
    """
    Chat with uploaded documents.

    FLOW:
    -----
    Question
        ↓
    Chat Service
        ↓
    RAG Pipeline
        ↓
    Grounded Answer
    """

    response = chat_with_documents(

        question=request.question,

        document_id=request.document_id
    )

    return response