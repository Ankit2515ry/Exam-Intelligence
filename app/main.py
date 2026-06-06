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


# =========================================================
# CREATE FASTAPI APP
# =========================================================

app = FastAPI(

    title="Exam Intelligence API",

    version="1.0.0",

    description=(
        "AI-Powered Exam Preparation "
        "and RAG System"
    )
)


# =========================================================
# CORS MIDDLEWARE
# =========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# REGISTER ROUTERS
# =========================================================

app.include_router(
    upload_router
)

app.include_router(
    chat_router
)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"]
)


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