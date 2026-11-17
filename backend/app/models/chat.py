"""
Chat Models

Responsibilities:
-----------------
1. Request schema validation
2. Response schema validation
3. Source citation structure

WHY MODELS ARE IMPORTANT:
-------------------------
Pydantic models provide:
- request validation
- response validation
- automatic API docs
- type safety
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, UUID4, field_validator


# =========================================================
# SOURCE MODEL
# =========================================================

class Source(BaseModel):
    """
    Source citation information.
    """

    page: Optional[int] = None

    chunk_id: Optional[str] = None

    document_id: Optional[str] = None

    content: Optional[str] = None

# =========================================================
# CHAT REQUEST
# =========================================================

class ChatRequest(BaseModel):
    """
    Incoming chat request.
    """

    # User question
    question: str

    # Number of retrieved chunks
    top_k: int = 5

    # Optional document filtering
    #
    # If provided:
    # retrieve only from one PDF
    #
    # If None:
    # search all uploaded PDFs
    document_id: Optional[UUID4] = None

    @field_validator("document_id", mode="before")
    @classmethod
    def validate_canonical_document_uuid(cls, value):
        if value is None:
            return value

        if not isinstance(value, str):
            raise ValueError("Document ID must be a UUID string")

        try:
            parsed = UUID(value)
        except ValueError as exc:
            raise ValueError("Document ID must be a valid UUID") from exc

        if str(parsed) != value.lower():
            raise ValueError("Document ID must use canonical UUID format")

        return parsed


# =========================================================
# CHAT RESPONSE
# =========================================================

class ChatResponse(BaseModel):
    """
    Final chat response.
    """

    question: str

    answer: str

    sources: List[Source]
