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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.chat import (
    ChatRequest,
    ChatResponse
)

from app.services.chat_service import (
    chat_with_documents
)

from app.auth.dependencies import get_current_user
from app.db.crud.document import get_document_by_uuid
from app.db.session import get_db

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
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
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

    document_uuid = (
        str(request.document_id)
        if request.document_id is not None
        else None
    )

    if document_uuid is not None:
        document = get_document_by_uuid(
            db=db,
            document_uuid=document_uuid
        )

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        if document.uploaded_by != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    response = chat_with_documents(

        question=request.question,

        user_id=current_user.id,

        document_id=document_uuid
    )

    return response
