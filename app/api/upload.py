"""# Import APIRouter
# Used to create modular API routes
from fastapi import APIRouter

# Import UploadFile
# Handles uploaded files efficiently
from fastapi import UploadFile

# Import File
# Tells FastAPI that this parameter is a file upload
from fastapi import File

# Import HTTPException
# Used for returning custom errors
from fastapi import HTTPException

# os module
# Used for folder creation and path handling
import os

# uuid module
# Used to generate unique document IDs
import uuid

# shutil module
# Used to copy uploaded file into local storage
import shutil


# Create API router object
router = APIRouter()


# Folder where uploaded PDFs will be stored
UPLOAD_DIR = "uploads"


# Create uploads folder if it does not exist
# exist_ok=True prevents error if folder already exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Create POST API endpoint
# Endpoint URL:
# POST /upload
@router.post("/upload")


# Async upload function
# Receives uploaded file from user
async def upload_pdf(

    # UploadFile -> uploaded file object
    # File(...) -> file is required
    file: UploadFile = File(...)
):


    # Validate uploaded file type
    # Only allow PDFs
    if file.content_type != "application/pdf":

        # Return error if uploaded file is not PDF
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
        
        # # Supported file MIME types
        # #
        # # Currently supported:
        # #
        # # PDF  -> application/pdf
        # # TXT  -> text/plain
        # # DOCX -> Microsoft Word documents
        # # PPTX -> Microsoft PowerPoint documents
        # # PNG  -> PNG images
        # # JPEG -> JPEG/JPG images
        # #
        # # In future:
        # # - PDFs can use PyMuPDF
        # # - DOCX can use python-docx
        # # - PPTX can use python-pptx
        # # - Images can use OCR pipelines
        # #
        # # This makes system extensible for future RAG support.
        # ALLOWED_TYPES = [

        #     # PDF files
        #     "application/pdf",

        #     # Plain text files
        #     "text/plain",

        #     # DOCX files
        #     "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

        #     # PPTX files
        #     "application/vnd.openxmlformats-officedocument.presentationml.presentation",

        #     # PNG image files
        #     "image/png",

        #     # JPEG/JPG image files
        #     "image/jpeg"
        # ]


        # # Validate uploaded file type
        # #
        # # If uploaded file MIME type is NOT inside
        # # ALLOWED_TYPES list,
        # # return error response.
        # if file.content_type not in ALLOWED_TYPES:

        #     raise HTTPException(

        #         # 400 -> Bad Request
        #         status_code=400,

        #         # Error message returned to user
        #         detail="Unsupported file type"
        #     )
    


    # Generate unique document ID
    # Example:
    # 8d92ab56-cdb7-4db4
    document_id = str(uuid.uuid4())


    # Create document folder path
    # Example:
    # uploads/8d92ab56/
    document_folder = os.path.join(
        UPLOAD_DIR,
        document_id
    )


    # Create document folder
    os.makedirs(document_folder)


    # Create full file path
    # Example:
    # uploads/8d92ab56/DBMS.pdf
    file_path = os.path.join(
        document_folder,
        file.filename
    )


    # Open file in binary write mode
    # "wb" means:
    # w -> write
    # b -> binary
    with open(file_path, "wb") as buffer:


        # Copy uploaded file into local storage
        shutil.copyfileobj(
            file.file,
            buffer
        )


    # Return JSON response
    return {

        # Unique document identifier
        "document_id": document_id,

        # Original uploaded filename
        "filename": file.filename,

        # Upload status
        "status": "uploaded"
    }
"""
"""
# Import APIRouter
# Used to create modular API routes
from fastapi import APIRouter

# Import UploadFile
# Handles uploaded files efficiently
from fastapi import UploadFile

# Import File
# Tells FastAPI that this parameter is a file upload
from fastapi import File

# Import HTTPException
# Used for returning custom errors
from fastapi import HTTPException

# Import FileResponse
# Used to open/view PDF in browser
from fastapi.responses import FileResponse

# os module
# Used for folder creation and path handling
import os

# uuid module
# Used to generate unique document IDs
import uuid

# shutil module
# Used to copy uploaded file into local storage
import shutil

# json module
# Used to store document metadata/history
import json


# Create API router object
router = APIRouter()


# Folder where uploaded PDFs will be stored
UPLOAD_DIR = "uploads"


# Metadata JSON file
# Stores upload history
METADATA_FILE = "documents.json"


# Create uploads folder if it does not exist
# exist_ok=True prevents error if folder already exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Create metadata file if it does not exist
#
# Example:
# documents.json
#
# [
#     {
#         "document_id": "...",
#         "filename": "...",
#         "path": "..."
#     }
# ]
if not os.path.exists(METADATA_FILE):

    with open(METADATA_FILE, "w") as f:
        json.dump([], f)



# Create POST API endpoint
# Endpoint URL:
# POST /upload
@router.post("/upload")


# Async upload function
# Receives uploaded file from user
async def upload_pdf(

    # UploadFile -> uploaded file object
    # File(...) -> file is required
    file: UploadFile = File(...)
):


    # Validate uploaded file type
    # Only allow PDFs
    if file.content_type != "application/pdf":

        # Return error if uploaded file is not PDF
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )


    # Generate unique document ID
    # Example:
    # 8d92ab56-cdb7-4db4
    document_id = str(uuid.uuid4())


    # Create document folder path
    # Example:
    # uploads/8d92ab56/
    document_folder = os.path.join(
        UPLOAD_DIR,
        document_id
    )


    # Create document folder
    os.makedirs(document_folder)


    # Create full file path
    # Example:
    # uploads/8d92ab56/DBMS.pdf
    file_path = os.path.join(
        document_folder,
        file.filename
    )


    # Open file in binary write mode
    # "wb" means:
    # w -> write
    # b -> binary
    with open(file_path, "wb") as buffer:


        # Copy uploaded file into local storage
        shutil.copyfileobj(
            file.file,
            buffer
        )


    # Create document metadata object
    document_data = {

        # Unique document identifier
        "document_id": document_id,

        # Original uploaded filename
        "filename": file.filename,

        # File storage path
        "path": file_path,

        # Upload status
        "status": "uploaded"
    }


    # Read existing metadata from documents.json
    with open(METADATA_FILE, "r") as f:
        documents = json.load(f)


    # Add newly uploaded document
    documents.append(document_data)


    # Save updated metadata back into JSON file
    with open(METADATA_FILE, "w") as f:
        json.dump(documents, f, indent=4)


    # Return JSON response
    return document_data



# GET ALL DOCUMENTS API
#
# Endpoint:
# GET /documents
#
# Purpose:
# Returns list of all uploaded documents
#
# Future frontend flow:
#
# GET /documents
#       ↓
# Show uploaded files
@router.get("/documents")
def get_documents():


    # Open metadata file
    with open(METADATA_FILE, "r") as f:

        # Read all documents
        documents = json.load(f)


    # Return all uploaded documents
    return documents



# VIEW DOCUMENT API
#
# Endpoint:
# GET /view/{document_id}
#
# Purpose:
# Open original PDF in browser
#
# Future frontend flow:
#
# User clicks PDF
#       ↓
# GET /view/{document_id}
#       ↓
# PDF viewer opens
@router.get("/view/{document_id}")
def view_document(document_id: str):


    # Open metadata file
    with open(METADATA_FILE, "r") as f:

        # Read stored documents
        documents = json.load(f)


    # Search matching document
    for doc in documents:


        # Check matching document ID
        if doc["document_id"] == document_id:


            # Return PDF file response
            #
            # Browser automatically:
            # - opens PDF
            # - previews document
            return FileResponse(

                # Original PDF path
                path=doc["path"],

                # MIME type for PDF
                media_type="application/pdf"
            )


    # If document ID not found
    raise HTTPException(
        status_code=404,
        detail="Document not found"
    )
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

import shutil
import os
import uuid
import json

from app.services.parser import PDFParser


router = APIRouter(
    prefix="/api",
    tags=["Upload"]
)


UPLOAD_DIR = "app/uploads"

METADATA_FILE = "documents.json"


os.makedirs(UPLOAD_DIR, exist_ok=True)


# Create metadata file if not exists
if not os.path.exists(METADATA_FILE):

    with open(METADATA_FILE, "w") as f:
        json.dump([], f)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # Validate PDF
    if file.content_type != "application/pdf":

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Generate unique document ID
    document_id = str(uuid.uuid4())

    # Create document folder
    document_folder = os.path.join(
        UPLOAD_DIR,
        document_id
    )

    os.makedirs(document_folder)

    # File path
    file_path = os.path.join(
        document_folder,
        file.filename
    )

    # Save file
    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # Parse PDF
    parser = PDFParser(file_path)

    parsed_data = parser.parse()

    # Store metadata
    document_data = {

        "document_id": document_id,

        "filename": file.filename,

        "path": file_path,

        "total_pages": len(parsed_data),

        "status": "parsed"
    }

    # Read metadata
    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    # Add document
    documents.append(document_data)

    # Save metadata
    with open(METADATA_FILE, "w") as f:

        json.dump(documents, f, indent=4)

    return {

        "message": "PDF uploaded and parsed successfully",

        "document": document_data,

        "pages": parsed_data
    }


@router.get("/documents")
def get_documents():

    # Read metadata
    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    valid_documents = []

    # Keep only valid documents
    for doc in documents:

        if os.path.exists(doc["path"]):

            valid_documents.append(doc)

    # Rewrite cleaned metadata file
    with open(METADATA_FILE, "w") as f:

        json.dump(valid_documents, f, indent=4)

    return valid_documents

@router.get("/view/{document_id}")
def view_document(document_id: str):

    # Read metadata
    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    for doc in documents:

        if doc["document_id"] == document_id:

            # Check if file actually exists
            if not os.path.exists(doc["path"]):

                raise HTTPException(
                    status_code=404,
                    detail="File missing from storage"
                )

            return FileResponse(
                path=doc["path"],
                media_type="application/pdf"
            )

    raise HTTPException(
        status_code=404,
        detail="Document not found"
    )


@router.delete("/delete/{document_id}")
def delete_document(document_id: str):

    # Read metadata
    with open(METADATA_FILE, "r") as f:

        documents = json.load(f)

    updated_documents = []

    found = False

    for doc in documents:

        # Matching document
        if doc["document_id"] == document_id:

            found = True

            # Delete actual PDF
            if os.path.exists(doc["path"]):

                os.remove(doc["path"])

            # Delete empty folder
            folder_path = os.path.dirname(doc["path"])

            if os.path.exists(folder_path):

                os.rmdir(folder_path)

        else:

            updated_documents.append(doc)

    # Save updated metadata
    with open(METADATA_FILE, "w") as f:

        json.dump(updated_documents, f, indent=4)

    if not found:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "message": "Document deleted successfully"
    }