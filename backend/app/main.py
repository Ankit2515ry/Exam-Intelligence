"""
Main FastAPI Application

Responsibilities:
-----------------
1. Create FastAPI app
2. Register API routers
3. Configure middleware
4. Configure metadata

IMPORTANT:
-----------
This file should remain lightweight.

It should NOT contain:
----------------------
- retrieval logic
- ingestion logic
- vector DB operations
- prompt engineering
"""

from fastapi import FastAPI

import app.db.models

from fastapi.middleware.cors import (
    CORSMiddleware
)


# =========================================================
# IMPORT ROUTERS
# =========================================================

from app.api.upload import (
    router as upload_router
)

from app.api.chat import (
    router as chat_router
)

from app.auth.routes import (
    router as auth_router
)
import shutil

print("TESSERACT PATH =", shutil.which("tesseract"))

# =========================================================
# CREATE FASTAPI APP
# =========================================================
print("step 1: Creating FastAPI app")
app = FastAPI(

    title="Exam Intelligence API",

    version="1.0.0",

    description=(
        "AI-Powered Exam Preparation "
        "and RAG System"
    )
)

print("step 2: FastAPI app created successfully")
# =========================================================
# CORS MIDDLEWARE
# =========================================================
print("step 3: Configuring CORS middleware")
app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)
print("step 4: CORS middleware configured successfully")
# app.add_middleware(

#     CORSMiddleware,
#     allow_origins=[
#         "http://your-frontend.vercel.app"
#     ],
#     allow_credentials=True,

#     allow_methods=["*"],

#     allow_headers=["*"],
# )


# =========================================================
# REGISTER ROUTERS
# =========================================================
print("step 5: Registering API routers")
app.include_router(
    upload_router
)
print("step 6: API routers registered successfully")
app.include_router(
    chat_router
)
print("step 7: Chat router registered successfully")

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"]
)

print("step 8: Auth router registered successfully")
# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def home():
    """
    Health check endpoint.
    """

    return {

        "message": (
            "Exam Intelligence API Running"
        ),

        "status": "healthy"
    }
print("step 9: Health check endpoint configured successfully")