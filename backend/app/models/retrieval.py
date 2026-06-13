"""
Retrieval Models

Responsibilities:
-----------------
Defines schemas for retrieval outputs.

WHY THIS MODEL IS IMPORTANT:
----------------------------
Retriever output is the foundation
for:
- reranking
- prompt building
- citations
- evaluation

Pipeline:
---------
Query
 ↓
Retriever
 ↓
RetrievedChunk
 ↓
Reranker
 ↓
Prompt Builder
"""

from typing import Dict, Any, List, Optional

from pydantic import BaseModel


# =========================================================
# RETRIEVED CHUNK
# =========================================================

class RetrievedChunk(BaseModel):
    """
    Represents one retrieved chunk.
    """

    # Retrieved chunk text
    text: str

    # Vector similarity score
    score: float

    # Optional reranking score
    rerank_score: Optional[float] = None

    # Optional hybrid score
    hybrid_score: Optional[float] = None

    # Optional BM25 score
    bm25_score: Optional[float] = None

    # Unique chunk identifier
    chunk_id: Optional[str] = None

    # Metadata for citations/filtering
    metadata: Dict[str, Any]


# =========================================================
# RETRIEVAL RESPONSE
# =========================================================

class RetrievalResponse(BaseModel):
    """
    Retrieval pipeline response.
    """

    # Original user query
    question: str

    # Retrieved chunks
    results: List[RetrievedChunk]