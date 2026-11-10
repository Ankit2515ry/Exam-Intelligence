"""
Upload API Routes

Responsibilities:
-----------------
1. Handle file uploads
2. Return uploaded documents
3. View PDFs
4. Delete documents
5. Expose chunk APIs


"""

import logging

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends
)

from fastapi.responses import (
    FileResponse
)

from sqlalchemy.orm import Session

import shutil
import os
import uuid



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

from app.db.session import get_db

from app.auth.dependencies import (
    get_current_user
)

from app.db.models.user import User

from app.db.crud.document import (

    create_document,

    get_user_documents,

    get_document_by_uuid,

    delete_document_record
)

logger = logging.getLogger(__name__)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(

    prefix="/api",

    tags=["Upload"]
)





# =========================================================
# STORAGE SETUP
# =========================================================



os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

os.makedirs(
    CHUNKS_DIR,
    exist_ok=True
)

\


# =========================================================
# UPLOAD PDF
# =========================================================

@router.post("/upload")
async def upload_pdf(

    file: UploadFile = File(...),

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)
):

    """
    Upload and process PDF.
    """

    logger.info("PDF upload received for user_id=%s", current_user.id)

    # -----------------------------------------------------
    # VALIDATE FILE TYPE
    # -----------------------------------------------------

    if file.content_type != "application/pdf":

        logger.warning(
            "Rejected upload with unsupported content type for user_id=%s",
            current_user.id,
        )
        raise HTTPException(

            status_code=400,

            detail="Only PDF files are allowed"
        )

    # -----------------------------------------------------
    # GENERATE DOCUMENT UUID
    # -----------------------------------------------------

    document_uuid = str(uuid.uuid4())

    # -----------------------------------------------------
    # CREATE DOCUMENT FOLDER
    # -----------------------------------------------------

    document_folder = os.path.join(
        UPLOAD_DIR,
        document_uuid
    )

    os.makedirs(
        document_folder,
        exist_ok=True
    )

    # -----------------------------------------------------
    # SAVE FILE
    # -----------------------------------------------------

    file_path = os.path.join(
        document_folder,
        file.filename
    )



    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # -----------------------------------------------------
    # STORE DOCUMENT IN DATABASE
    # -----------------------------------------------------

    document = create_document(

        db=db,

        title=file.filename,

        filename=file.filename,

        file_path=file_path,

        subject="General",

        uploaded_by=current_user.id,

        document_uuid=document_uuid
    )

    # -----------------------------------------------------
    # INGEST DOCUMENT
    # -----------------------------------------------------

    try:
        ingestion_result = ingest_document(
            file_path=file_path,
            db=db,
            document_db_id=document.id,
            document_uuid=document.document_uuid,
            user_id=current_user.id,
        )
    except Exception:
        logger.exception(
            "PDF ingestion failed for document_uuid=%s user_id=%s",
            document.document_uuid,
            current_user.id,
        )
        raise

    logger.info(
        "PDF ingestion completed for document_uuid=%s pages=%s chunks=%s",
        document.document_uuid,
        ingestion_result["total_pages"],
        ingestion_result["total_chunks"],
    )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "message": (
            "PDF uploaded successfully"
        ),

        "document": {

            "id": document.id,

            "document_uuid": (
                document.document_uuid
            ),

            "filename": (
                document.filename
            ),

            "uploaded_by": (
                current_user.email
            ),

            "total_pages": (
                ingestion_result["total_pages"]
            ),

            "total_chunks": (
                ingestion_result["total_chunks"]
            )
        }
    }


# =========================================================
# GET USER DOCUMENTS
# =========================================================

@router.get("/documents")
def get_documents(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)
):

    documents = get_user_documents(

        db=db,

        user_id=current_user.id
    )

    return documents


# =========================================================
# VIEW DOCUMENT
# =========================================================

@router.get("/view/{document_uuid}")
def view_document(

    document_uuid: str,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)
):

    document = get_document_by_uuid(

        db=db,

        document_uuid=document_uuid
    )

    if document is None:

        raise HTTPException(

            status_code=404,

            detail="Document not found"
        )

    # -----------------------------------------------------
    # SECURITY CHECK
    # -----------------------------------------------------

    if document.uploaded_by != current_user.id:

        raise HTTPException(

            status_code=403,

            detail="Access denied"
        )

    # -----------------------------------------------------
    # FILE EXISTS?
    # -----------------------------------------------------

    if not os.path.exists(
        document.file_path
    ):

        raise HTTPException(

            status_code=404,

            detail="PDF file missing"
        )

    return FileResponse(

        path=document.file_path,

        media_type="application/pdf"
    )


# =========================================================
# GET SINGLE CHUNK
# =========================================================

@router.get("/chunk/{chunk_id}")
def get_chunk(

    chunk_id: str,

    current_user: User = Depends(
        get_current_user
    )
):

    # print("Requested chunk ID:", chunk_id)
    results = get_chunk_by_id(
        chunk_id
    )

    if not results["ids"]:

        raise HTTPException(

            status_code=404,

            detail="Chunk not found"
        )

    metadata = results["metadatas"][0]

    # -----------------------------------------------------
    # SECURITY CHECK
    # -----------------------------------------------------

    # print("Metadata user_id:", metadata.get("user_id"))
    # print("Current user id:", current_user.id)
    if metadata.get("user_id") != current_user.id:

        raise HTTPException(

            status_code=403,

            detail="Access denied"
        )

    return {

        "chunk_id": results["ids"][0],

        "text": results["documents"][0],

        "metadata": metadata
    }


# =========================================================
# GET DOCUMENT CHUNKS
# =========================================================

@router.get("/chunks/{document_uuid}")
def get_chunks(

    document_uuid: str,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)
):

    document = get_document_by_uuid(

        db=db,

        document_uuid=document_uuid
    )

    if document is None:

        raise HTTPException(

            status_code=404,

            detail="Document not found"
        )

    # -----------------------------------------------------
    # SECURITY CHECK
    # -----------------------------------------------------

    if document.uploaded_by != current_user.id:

        raise HTTPException(

            status_code=403,

            detail="Access denied"
        )

    results = get_document_chunks(
        document_uuid
    )

    return results


# =========================================================
# DELETE DOCUMENT
# =========================================================

@router.delete("/delete/{document_uuid}")
def delete_document(

    document_uuid: str,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db)
):

    document = get_document_by_uuid(

        db=db,

        document_uuid=document_uuid
    )

    if document is None:

        raise HTTPException(

            status_code=404,

            detail="Document not found"
        )

    # -----------------------------------------------------
    # SECURITY CHECK
    # -----------------------------------------------------

    if document.uploaded_by != current_user.id:

        raise HTTPException(

            status_code=403,

            detail="Access denied"
        )

    # -----------------------------------------------------
    # DELETE CHROMADB VECTORS
    # -----------------------------------------------------

    delete_document_chunks(
        document_uuid
    )

    # -----------------------------------------------------
    # DELETE PDF FILE
    # -----------------------------------------------------

    if os.path.exists(
        document.file_path
    ):

        os.remove(document.file_path)

    # -----------------------------------------------------
    # DELETE EMPTY FOLDER
    # -----------------------------------------------------

    folder_path = os.path.dirname(
        document.file_path
    )

    if os.path.exists(folder_path):

        os.rmdir(folder_path)

    # -----------------------------------------------------
    # DELETE DATABASE RECORD
    # -----------------------------------------------------

    delete_document_record(

        db=db,

        document=document
    )

    return {

        "message": (
            "Document deleted successfully"
        ),

        "document_uuid": document_uuid
    }


"""
=========================================================
UPLOAD.PY - COMPLETE UNDERSTANDING SUMMARY
=========================================================

1. ROLE OF UPLOAD.PY
--------------------
- upload.py contains document-related API routes.
- It handles PDF upload, document listing, PDF viewing,
  chunk retrieval and document deletion.
- It acts as a coordination layer between API endpoints,
  authentication, database helpers and backend services.
- It uses FastAPI APIRouter.
- It should not contain complex PDF processing or RAG logic.
- Heavy processing is delegated to ingestion_service.py.

2. PYTHON IMPORTS
-----------------
FASTAPI IMPORTS:
- APIRouter: Creates a group of related API endpoints.
- UploadFile: Represents an uploaded file.
- File: Declares file upload parameters.
- HTTPException: Raises HTTP errors.
- Depends: Implements dependency injection.

OTHER IMPORTS:
- FileResponse: Returns files such as PDFs as HTTP responses.
- Session: Represents a SQLAlchemy database session.
- os: Handles file and directory operations.
- shutil: Provides file utilities.
- uuid: Generates unique identifiers.

PROJECT IMPORTS:
- UPLOAD_DIR: Configured PDF upload directory.
- CHUNKS_DIR: Configured chunks directory.
- ingest_document: Processes uploaded documents.
- get_chunk_by_id: Retrieves a particular vector-store chunk.
- get_document_chunks: Retrieves chunks of a document.
- delete_document_chunks: Deletes document vectors.
- get_db: Provides a database session.
- get_current_user: Provides authenticated user information.
- User: SQLAlchemy user model.
- create_document: Creates a document database record.
- get_user_documents: Retrieves a user's documents.
- get_document_by_uuid: Finds a document using UUID.
- delete_document_record: Deletes a document database record.

3. APIRouter CONFIGURATION
--------------------------
- router = APIRouter() creates a router object.
- prefix="/api" adds /api to every endpoint in this router.
- tags=["Upload"] groups endpoints in API documentation.
- main.py registers this router using include_router().

4. STORAGE DIRECTORY SETUP
--------------------------
- UPLOAD_DIR defines the main PDF storage directory.
- CHUNKS_DIR defines a configured chunks directory.
- os.makedirs() creates directories.
- exist_ok=True prevents an error if a directory
  already exists.
- These directory creation statements execute when
  the module is imported.

5. UPLOAD PDF ENDPOINT
----------------------
- @router.post("/upload") registers a POST endpoint.
- Full endpoint: POST /api/upload.
- upload_pdf() receives and processes a PDF upload.
- UploadFile represents the uploaded file.
- File(...) makes the file parameter required.
- Depends(get_current_user) provides the authenticated user.
- Depends(get_db) provides a database session.

6. FILE VALIDATION
------------------
- file.content_type contains the declared MIME type.
- "application/pdf" represents the PDF MIME type.
- HTTPException is used to return an HTTP error.
- Status code 400 represents a bad request.
- MIME type checking alone does not prove that the file
  actually contains valid PDF data.

7. DOCUMENT UUID GENERATION
---------------------------
- uuid.uuid4() generates a random UUID.
- UUID stands for Universally Unique Identifier.
- str() converts the UUID object into a string.
- document_uuid uniquely identifies an uploaded document.
- It is independent of the original filename.

8. DIRECTORY AND FILE HANDLING
------------------------------
- os.path.join() constructs file and directory paths.
- os.makedirs() creates a document-specific directory.
- open(file_path, "wb") opens a file in binary write mode.
- "wb" is used for writing binary data.
- shutil.copyfileobj() copies file bytes from the uploaded
  file stream into the destination file.
- file.file provides access to the underlying file stream.

SECURITY CONSIDERATIONS:
- Client-provided filenames must be handled safely.
- File-size limits should be implemented.
- File contents should be validated.
- Paths must remain inside the intended upload directory.

9. DATABASE DOCUMENT CREATION
-----------------------------
- create_document() creates a document database record.
- It receives the database session and document details.
- title stores the document title.
- filename stores the original filename.
- file_path stores the file location.
- uploaded_by stores the authenticated user's ID.
- document_uuid stores the document UUID.
- subject is currently set to "General".
- The helper is responsible for database persistence.

10. DOCUMENT INGESTION
----------------------
- ingest_document() is called after the file is saved
  and the document record is created.
- It is imported from ingestion_service.py.
- It receives:
    a. file_path
    b. db
    c. document_db_id
    d. document_uuid
    e. user_id

- The ingestion service handles document processing.
- It returns information such as total_pages and total_chunks.
- Actual PDF parsing, chunking, embeddings and vector
  storage should be studied inside the ingestion service
  and its dependent modules.

11. UPLOAD RESPONSE
------------------
- The endpoint returns a Python dictionary.
- FastAPI converts it into a JSON response.
- Response includes:
    a. Success message
    b. Document ID
    c. Document UUID
    d. Filename
    e. Uploader email
    f. Total pages
    g. Total chunks

12. LIST USER DOCUMENTS
-----------------------
- Endpoint: GET /api/documents.
- Function: get_documents().
- Uses get_current_user to identify the user.
- Uses get_db to obtain a database session.
- Calls get_user_documents().
- Returns documents belonging to the current user.

13. VIEW DOCUMENT
-----------------
- Endpoint: GET /api/view/{document_uuid}.
- Function: view_document().
- Retrieves the document using its UUID.
- Checks whether the document exists.
- Verifies document ownership.
- Checks whether the PDF file exists.
- Returns FileResponse to send the PDF to the client.
- HTTP 404 means the document or file was not found.
- HTTP 403 means access is forbidden.

14. GET SINGLE CHUNK
--------------------
- Endpoint: GET /api/chunk/{chunk_id}.
- Function: get_chunk().
- Retrieves a chunk from the vector database.
- Checks whether the chunk exists.
- Reads the chunk metadata.
- Compares metadata user_id with current_user.id.
- Returns chunk ID, text and metadata.
- Uses HTTP 404 for missing chunks.
- Uses HTTP 403 for unauthorized access.

15. GET DOCUMENT CHUNKS
-----------------------
- Endpoint: GET /api/chunks/{document_uuid}.
- Function: get_chunks().
- Retrieves the document using UUID.
- Checks document existence.
- Verifies ownership.
- Calls get_document_chunks().
- Returns the document's chunks.

16. DELETE DOCUMENT
-------------------
- Endpoint: DELETE /api/delete/{document_uuid}.
- Function: delete_document().
- Retrieves the document using UUID.
- Checks whether the document exists.
- Verifies document ownership.

DELETION SEQUENCE:
1. Delete document vectors from ChromaDB.
2. Delete the original PDF file.
3. Remove the empty document folder.
4. Delete the relational database record.
5. Return a success response.

17. AUTHENTICATION AND AUTHORIZATION
------------------------------------
- Authentication identifies who the user is.
- Authorization checks what the user is allowed to access.
- get_current_user provides the authenticated user.
- Ownership checks compare uploaded_by with current_user.id.
- A document UUID alone should not grant document access.
- HTTP 403 represents forbidden access.
- HTTP 404 represents a missing resource.

18. DEPENDENCY INJECTION
-----------------------
- Depends() is a FastAPI dependency injection mechanism.
- get_current_user provides authenticated user information.
- get_db provides a SQLAlchemy database session.
- FastAPI resolves dependencies and passes their results
  into endpoint function parameters.

19. IMPORTANT PYTHON CONCEPTS
-----------------------------
- async def: Defines an asynchronous function.
- UUID: Unique identifier.
- MIME type: Describes the declared media type of a file.
- Binary mode: Handles raw bytes.
- os.path.join(): Combines path components.
- os.path.exists(): Checks file or directory existence.
- os.remove(): Deletes a file.
- os.rmdir(): Removes an empty directory.
- FileResponse: Sends a file as an HTTP response.

20. ARCHITECTURAL CONCERNS
--------------------------
- Synchronous file copying inside async endpoints can block
  the event loop.
- Synchronous ingestion can also block request handling.
- File creation, database commits and vector writes are
  separate operations.
- Partial failures can leave incomplete document data.
- Upload filename validation and file-size limits are important.
- Explicit error handling and cleanup are needed.
- Large processing workflows may benefit from background jobs.

21. OVERALL UPLOAD WORKFLOW
---------------------------
1. Frontend sends a PDF upload request.
2. FastAPI receives the file.
3. Authentication dependency identifies the user.
4. Database dependency provides a session.
5. File type is checked.
6. Document UUID is generated.
7. Document folder is created.
8. PDF is saved locally.
9. Document record is created in the database.
10. ingest_document() processes the PDF.
11. Ingestion result is received.
12. JSON response is returned to the frontend.

=========================================================
END OF UPLOAD.PY SUMMARY
=========================================================
"""
