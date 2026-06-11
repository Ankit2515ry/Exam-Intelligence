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

from sqlalchemy.orm import Session

from app.db.crud.chunk import (
    create_chunk
)

# =========================================================
# INGEST DOCUMENT
# =========================================================

def ingest_document(
    file_path: str,
    db: Session,
    document_db_id: int,
    document_uuid: str,
    user_id: int
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

    # document_id = str(uuid.uuid4())

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

        document_id=document_uuid,

        user_id=user_id
    )

    # =====================================================
    # STORE IN VECTOR DB
    # =====================================================

    store_chunks(chunks)

    # =====================================================
    # STORE CHUNK METADATA IN POSTGRESQL
    # =====================================================

    for index, chunk in enumerate(chunks):

        metadata = chunk["metadata"]

        create_chunk(

            db=db,

            document_id=document_db_id,

            chunk_index=index,

            content=chunk["text"],

            chroma_id=str(uuid.uuid4()),

            page_number=metadata.get(
                "page",
                1
            ),

            chunk_metadata=metadata
        )
    # =====================================================
    # RETURN INGESTION RESULT
    # =====================================================

    return {

        "status": "success",
        
        "total_pages": len(parsed_pages),

        "total_chunks": len(chunks)
    }