"""
Query Models

Responsibilities:
-----------------
Defines retrieval query schemas.

WHY THIS MODEL EXISTS:
----------------------
Separates:
- retrieval requests
from
- chat responses

Useful for:
------------
- retrieval APIs
- evaluation pipelines
- testing retrieval quality
- hybrid search experimentation
"""

from typing import Optional

from pydantic import BaseModel


# =========================================================
# QUERY REQUEST
# =========================================================

class QueryRequest(BaseModel):
    """
    Retrieval query request.
    """

    # User question
    question: str

    # Number of chunks to retrieve
    top_k: int = 5

    # Optional metadata filtering
    #
    # If provided:
    # search only one document
    document_id: Optional[str] = None