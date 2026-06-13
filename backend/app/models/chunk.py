"""
Chunk Model

Responsibilities:
-----------------
Defines the structure of a document chunk.

WHY CHUNKS ARE IMPORTANT:
-------------------------
Chunks are the core retrieval units
inside the RAG pipeline.

Workflow:
---------
PDF
 ↓
Chunk
 ↓
Embedding
 ↓
Vector DB
 ↓
Retrieval

This schema supports:
- source citations
- metadata filtering
- reranking
- hierarchical chunking
- future analytics
"""

from typing import Optional, Dict, Any

from pydantic import BaseModel



# =========================================================
# CHUNK MODEL
# =========================================================

class Chunk(BaseModel):
    """
    Represents a single document chunk.
    """

    # Unique chunk identifier
    chunk_id: str

    # Parent document identifier
    document_id: str

    # Actual chunk text
    text: str

    # Original PDF page number
    page: int

    # Chunk order inside document
    chunk_index: int

    # Optional hierarchical metadata
    #
    # Future use:
    # chapter-aware retrieval
    chapter: Optional[str] = None

    # Optional section title
    section: Optional[str] = None

    # Flexible metadata storage
    #
    # Future use:
    # - subject
    # - headings
    # - semantic tags
    # - difficulty
    # - OCR confidence
    metadata: Optional[
        Dict[str, Any]
    ] = None