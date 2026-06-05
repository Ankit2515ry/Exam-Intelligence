"""
Ingestion Service

Responsibilities:
-----------------
1. Coordinate PDF ingestion workflow
2. Parse uploaded documents
3. Create chunks
4. Store embeddings in vector DB

WHY THIS SERVICE EXISTS:
------------------------
This service orchestrates the complete
document ingestion pipeline.

Workflow:
---------
PDF
 ↓
Parser
 ↓
Chunker
 ↓
Embeddings
 ↓
Vector DB

This layer coordinates the process,
while low-level logic remains inside:
- rag/parser.py
- rag/chunker.py
- rag/vectordb.py
"""

import uuid
from typing import Dict

from app.rag.parser import PDFParser

from app.rag.chunker import (
    create_chunks
)

from app.rag.vectordb import (
    store_chunks
)


# =========================================================
# INGEST DOCUMENT
# =========================================================

def ingest_document(
    file_path: str
) -> Dict:
    """
    Process uploaded PDF document.

    PARAMETERS:
    -----------
    file_path:
        Path to uploaded PDF

    RETURNS:
    --------
    Document ingestion summary
    """

    # =====================================================
    # GENERATE DOCUMENT ID
    # =====================================================

    """
    Unique identifier for the document.

    WHY IMPORTANT?
    --------------
    Used for:
    - metadata filtering
    - citations
    - document isolation
    - deletion
    """

    document_id = str(uuid.uuid4())

    # =====================================================
    # PARSE PDF
    # =====================================================

    parser = PDFParser(file_path)

    parsed_pages = parser.parse()

    # =====================================================
    # CREATE CHUNKS
    # =====================================================

    chunks = create_chunks(

        pages=parsed_pages,

        document_id=document_id
    )

    # =====================================================
    # STORE IN VECTOR DB
    # =====================================================

    store_chunks(chunks)

    # =====================================================
    # RETURN INGESTION RESULT
    # =====================================================

    return {

        "status": "success",

        "document_id": document_id,

        "total_pages": len(parsed_pages),

        "total_chunks": len(chunks)
    }