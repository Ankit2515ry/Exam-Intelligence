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

from pydantic import BaseModel


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
    document_id: Optional[str] = None


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