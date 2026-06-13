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
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


# =========================================================
# PROJECT PATHS
# =========================================================

# Base project folders

UPLOAD_DIR = "uploads"

CHUNKS_DIR = "chunks"

VECTOR_DB_DIR = "chroma_db"


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