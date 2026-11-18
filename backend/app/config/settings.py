"""
Centralized application configuration.

WHY THIS FILE EXISTS:
---------------------
Instead of hardcoding values across multiple files,
we store all configurable settings in one place.

Benefits:
---------
1. Easy maintenance
2. Cleaner architecture
3. Production scalability
4. Easier experimentation
5. Environment-specific configs later

This file will be used by:
- chunker
- retriever
- vector db
- llm
- reranker
- services
"""

import os

from app.config.environment import load_application_environment


# Load environment variables from .env
load_application_environment()


# =========================================================
# PROJECT PATHS
# =========================================================

# Base project folders

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

CHUNKS_DIR = os.getenv("CHUNKS_DIR", "chunks")

VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "chroma_db")

# Maximum accepted PDF size. The upload route enforces this while streaming.
MAX_PDF_UPLOAD_SIZE_BYTES = int(
    os.getenv(
        "MAX_PDF_UPLOAD_SIZE_BYTES",
        str(25 * 1024 * 1024)
    )
)

if MAX_PDF_UPLOAD_SIZE_BYTES <= 0:
    raise ValueError(
        "MAX_PDF_UPLOAD_SIZE_BYTES must be greater than zero"
    )

# Optional absolute path to the Tesseract executable. When unset, pytesseract
# resolves the `tesseract` command through the operating system PATH.
TESSERACT_CMD = os.getenv("TESSERACT_CMD")


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# =========================================================
# CHUNKING CONFIGURATION
# =========================================================

# Maximum characters inside one chunk
CHUNK_SIZE = 250

# Overlapping characters between chunks
# Helps preserve context continuity
CHUNK_OVERLAP = 50


# =========================================================
# RETRIEVAL CONFIGURATION
# =========================================================

# Number of chunks retrieved initially
TOP_K = 5

# Number of chunks retrieved before reranking
RERANK_TOP_K = 10


# =========================================================
# EMBEDDING MODEL CONFIGURATION
# =========================================================

# Gemini embedding model
EMBEDDING_MODEL = "models/embedding-001"


# =========================================================
# LLM CONFIGURATION
# =========================================================

# Main LLM used for chat responses
LLM_MODEL = "gemini-2.5-flash"


# =========================================================
# API KEYS
# =========================================================

# Gemini API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# =========================================================
# CHROMA COLLECTION
# =========================================================

# Name of vector collection
COLLECTION_NAME = "exam_intelligence"


# =========================================================
# RERANKER CONFIGURATION
# =========================================================

# Cross-encoder reranker model
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# =========================================================
# HYBRID SEARCH WEIGHTS
# =========================================================

# Vector similarity contribution
VECTOR_WEIGHT = 0.7

# BM25 keyword contribution
BM25_WEIGHT = 0.3


# =========================================================
# DEBUG CONFIGURATION
# =========================================================

DEBUG = True

# =========================================================
# PERFORMANCE TELEMETRY
# =========================================================

PERFORMANCE_METRICS_ENABLED = os.getenv(
    "PERFORMANCE_METRICS_ENABLED", "false"
).lower() in {"1", "true", "yes", "on"}
PERFORMANCE_METRICS_PATH = os.getenv(
    "PERFORMANCE_METRICS_PATH", "metrics/performance.jsonl"
)
PERFORMANCE_METRICS_MAX_BYTES = int(os.getenv(
    "PERFORMANCE_METRICS_MAX_BYTES", str(5 * 1024 * 1024)
))
PERFORMANCE_METRICS_BACKUPS = int(os.getenv("PERFORMANCE_METRICS_BACKUPS", "3"))
PERFORMANCE_PROVIDER_MODE = os.getenv("PERFORMANCE_PROVIDER_MODE", "real")
PERFORMANCE_MEASUREMENT_CLASS = os.getenv("PERFORMANCE_MEASUREMENT_CLASS", "unclassified")
PERFORMANCE_RUN_TEMPERATURE = os.getenv("PERFORMANCE_RUN_TEMPERATURE") or None

if PERFORMANCE_METRICS_MAX_BYTES <= 0 or PERFORMANCE_METRICS_BACKUPS < 0:
    raise ValueError("Performance metric retention settings are invalid")
