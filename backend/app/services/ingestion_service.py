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

import logging
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

logger = logging.getLogger(__name__)
from app.observability.performance import current_event, stage, set_count, set_value

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

    logger.info(
        "Starting document ingestion document_uuid=%s user_id=%s",
        document_uuid,
        user_id,
    )

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

    set_value("ocr_used", False)
    with stage("pdf_parsing"):
        parsed_pages = parser.parse()
    event = current_event()
    if event is not None and event["durations_ms"]["ocr"] is not None:
        event["durations_ms"]["pdf_parsing"] = max(
            0.0,
            event["durations_ms"]["pdf_parsing"] - event["durations_ms"]["ocr"],
        )
    set_count("retained_pages", len(parsed_pages))

    # =====================================================
    # CREATE CHUNKS
    # =====================================================

    with stage("chunking"):
        chunks = create_chunks(
            pages=parsed_pages,
            document_id=document_uuid,
            user_id=user_id
        )
    set_count("chunks", len(chunks))
    logger.debug(
        "Created document chunks document_uuid=%s count=%s",
        document_uuid,
        len(chunks),
    )

    # =====================================================
    # STORE IN VECTOR DB
    # =====================================================

    store_chunks(chunks)
    logger.debug(
        "Stored document vectors document_uuid=%s count=%s",
        document_uuid,
        len(chunks),
    )

    # =====================================================
    # STORE CHUNK METADATA IN POSTGRESQL
    # =====================================================

    with stage("sql_persistence"):
        for index, chunk in enumerate(chunks):

            metadata = chunk["metadata"]

            create_chunk(

            db=db,

            document_id=document_db_id,

            chunk_index=index,

            content=chunk["text"],

            chroma_id=chunk["chunk_id"],

            page_number=metadata.get(
                "page",
                1
            ),

            chunk_metadata=metadata,

                commit=False
            )
    # =====================================================
    # RETURN INGESTION RESULT
    # =====================================================

    result = {

        "status": "success",
        
        "total_pages": len(parsed_pages),

        "total_chunks": len(chunks)
    }
    logger.info(
        "Document ingestion finished document_uuid=%s pages=%s chunks=%s",
        document_uuid,
        result["total_pages"],
        result["total_chunks"],
    )
    return result
