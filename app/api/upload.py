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

    # -----------------------------------------------------
    # VALIDATE FILE TYPE
    # -----------------------------------------------------

    if file.content_type != "application/pdf":

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

    ingestion_result = ingest_document(

        file_path=file_path,

        db=db,

        document_db_id=document.id,

        document_uuid=document.document_uuid,

        user_id=current_user.id
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

    print("Requested chunk ID:", chunk_id)
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

    print("Metadata user_id:", metadata.get("user_id"))
    print("Current user id:", current_user.id)
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