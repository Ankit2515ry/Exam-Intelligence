"""
Upload API Routes

Responsibilities:
-----------------
1. Handle file uploads
2. Return uploaded documents
3. View PDFs
4. Delete documents
5. Expose chunk APIs

IMPORTANT:
-----------
This layer should remain THIN.

It should:
-----------
- validate requests
- call services
- return responses

It should NOT:
---------------
- parse PDFs
- chunk text
- generate embeddings
- manipulate vector DB directly
"""

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from fastapi.responses import (
    FileResponse
)




import shutil
import os
import uuid
import json

from app.config.settings import (
    UPLOAD_DIR,
    CHUNKS_DIR
)

from app.services.ingestion_service import (
    ingest_document
)

from app.rag.vectordb import (
    get_chunk_by_id,
    get_document_chunks,
    delete_document_chunks
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(

    prefix="/api",

    tags=["Upload"]
)




# =========================================================
# METADATA STORAGE
# =========================================================

METADATA_FILE = "documents.json"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

os.makedirs(
    CHUNKS_DIR,
    exist_ok=True
)


# Create metadata file if missing
if not os.path.exists(METADATA_FILE):

    with open(METADATA_FILE, "w") as f:

        json.dump([], f)


# =========================================================
# UPLOAD PDF
# =========================================================

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):
    """
    Upload and process PDF.
    """

    # Validate file type
    if file.content_type != "application/pdf":

        raise HTTPException(

            status_code=400,

            detail=(
                "Only PDF files are allowed"
            )
        )

    # Generate unique document ID
    document_id = str(uuid.uuid4())

    # Create document folder
    document_folder = os.path.join(
        UPLOAD_DIR,
        document_id
    )

    os.makedirs(document_folder)

    # Save uploaded file
    file_path = os.path.join(
        document_folder,
        file.filename
    )


    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # =====================================================
    # INGEST DOCUMENT
    # =====================================================

    ingestion_result = ingest_document(
        file_path
    )

    # =====================================================
    # SAVE DOCUMENT METADATA
    # =====================================================

    document_data = {

        "document_id": (
            ingestion_result["document_id"]
        ),

        "filename": file.filename,

        "path": file_path,

        "total_pages": (
            ingestion_result["total_pages"]
        ),

        "total_chunks": (
            ingestion_result["total_chunks"]
        ),

        "status": "processed"
    }

    # Read metadata
    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    # Add document
    documents.append(document_data)

    # Save metadata
    with open(METADATA_FILE, "w") as f:

        json.dump(
            documents,
            f,
            indent=4
        )

    return {

        "message": (
            "PDF uploaded successfully"
        ),

        "document": document_data
    }


# =========================================================
# GET ALL DOCUMENTS
# =========================================================

@router.get("/documents")
def get_documents():


    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    valid_documents = []


    for doc in documents:

        if os.path.exists(doc["path"]):

            valid_documents.append(doc)

    # Cleanup stale entries
    with open(METADATA_FILE, "w") as f:

        json.dump(
            valid_documents,
            f,
            indent=4
        )

    return valid_documents


# =========================================================
# VIEW DOCUMENT
# =========================================================

@router.get("/view/{document_id}")
def view_document(document_id: str):


    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    for doc in documents:

        if doc["document_id"] == document_id:

            if not os.path.exists(
                doc["path"]
            ):

                raise HTTPException(

                    status_code=404,

                    detail=(
                        "File missing "
                        "from storage"
                    )
                )

            return FileResponse(

                path=doc["path"],

                media_type="application/pdf"
            )

    raise HTTPException(

        status_code=404,

        detail="Document not found"
    )


# =========================================================
# GET SINGLE CHUNK
# =========================================================

@router.get("/chunk/{chunk_id}")
def get_chunk(chunk_id: str):

    results = get_chunk_by_id(
        chunk_id
    )

    if not results["ids"]:

        raise HTTPException(

            status_code=404,

            detail="Chunk not found"
        )

    return {

        "chunk_id": results["ids"][0],

        "text": results["documents"][0],

        "metadata": results["metadatas"][0]
    }


# =========================================================
# GET DOCUMENT CHUNKS
# =========================================================

@router.get("/chunks/{document_id}")
def get_chunks(document_id: str):

    results = get_document_chunks(
        document_id
    )

    return results


# =========================================================
# DELETE DOCUMENT
# =========================================================

@router.delete("/delete/{document_id}")
def delete_document(document_id: str):


    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    updated_documents = []

    found = False

    for doc in documents:


        if doc["document_id"] == document_id:

            found = True

            # Delete vectors
            delete_document_chunks(
                document_id
            )

            # Delete original PDF
            if os.path.exists(doc["path"]):

                os.remove(doc["path"])

            # Delete folder
            folder_path = os.path.dirname(
                doc["path"]
            )

            if os.path.exists(folder_path):

                os.rmdir(folder_path)

        else:

            updated_documents.append(doc)

    # Save updated metadata
    with open(METADATA_FILE, "w") as f:

        json.dump(
            updated_documents,
            f,
            indent=4
        )



    if not found:

        raise HTTPException(

            status_code=404,

            detail="Document not found"
        )

    return {

        "message": (
            "Document deleted successfully"
        ),

        "document_id": document_id
    }