"""
Document Model

Responsibilities:
-----------------
Represents uploaded PDF metadata.

WHY THIS MODEL IS IMPORTANT:
----------------------------
Documents act as the parent entities
for all chunks.

Relationship:
-------------
Document
    ↓
Pages
    ↓
Chunks
    ↓
Embeddings

This model supports:
- document management
- metadata filtering
- upload tracking
- analytics
- document deletion
"""

from typing import Optional

from pydantic import BaseModel


# =========================================================
# DOCUMENT MODEL
# =========================================================

class Document(BaseModel):
    """
    Represents uploaded PDF document.
    """

    # Unique document identifier
    document_id: str

    # Original uploaded filename
    filename: str

    # Physical file storage path
    path: str

    # Total number of PDF pages
    total_pages: int

    # Total generated chunks
    total_chunks: int

    # Processing status
    #
    # Example:
    # processed
    # processing
    # failed
    status: str = "processed"

    # Optional upload timestamp
    uploaded_at: Optional[str] = None