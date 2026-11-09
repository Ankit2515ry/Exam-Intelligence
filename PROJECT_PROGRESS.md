# Exam Intelligence Project Learning Progress

This file is the project walkthrough checklist. We will follow the application
in runtime order, study one file at a time, and mark a file complete only after
its purpose, inputs, outputs, and connections to other files are understood.

## How to use this tracker

For each file:

1. Read the file together.
2. Explain its responsibility and important code.
3. Trace what calls it and what it calls.
4. Note unfamiliar concepts or questions.
5. Mark it complete when the walkthrough is understood.

Progress markers:

- `[ ]` Not started
- `[~]` In progress
- `[x]` Understood

Do not treat installed dependencies, virtual environments, generated build
files, or local database/vector-store contents as application source files.
The checklist below covers the repository's tracked project files.

## 1. Get the project running and understand its configuration

- [ ] `README.md` — project overview and setup
- [ ] `backend/runtime.txt` — backend runtime version
- [ ] `backend/requirements.txt` — Python dependencies
- [ ] `backend/important_commands.txt` — developer commands and setup notes
- [ ] `backend/.gitignore` — backend-generated and private files
- [ ] `backend/app/config/settings.py` — application and RAG configuration
- [ ] `frontend/exam_intelligence/README.md` — frontend starter documentation
- [ ] `frontend/exam_intelligence/package.json` — frontend scripts and dependencies
- [ ] `frontend/exam_intelligence/package-lock.json` — locked frontend dependency versions
- [ ] `frontend/exam_intelligence/.gitignore` — frontend-generated and private files

## 2. Follow application startup

### Frontend startup

- [ ] `frontend/exam_intelligence/index.html` — browser document and React mount point
- [ ] `frontend/exam_intelligence/src/main.jsx` — React entry point
- [ ] `frontend/exam_intelligence/src/App.jsx` — page routes
- [ ] `frontend/exam_intelligence/src/index.css` — global styles
- [ ] `frontend/exam_intelligence/vite.config.js` — Vite and Tailwind setup
- [ ] `frontend/exam_intelligence/eslint.config.js` — frontend lint rules

### Backend startup

- [ ] `backend/app/__init__.py` — backend application package
- [ ] `backend/app/main.py` — FastAPI app, middleware, and router registration
- [ ] `backend/app/api/__init__.py` — API package
- [ ] `backend/app/auth/routes.py` — authentication router registration and endpoints
- [ ] `backend/app/api/upload.py` — upload/document router registration and endpoints
- [ ] `backend/app/api/chat.py` — chat router registration and endpoint
- [ ] `backend/app/api/documents.py` — additional document API module; check whether it is used

## 3. Understand frontend screens and HTTP requests

### Request setup and API contracts

- [ ] `frontend/exam_intelligence/src/api/axiosInstance.js` — shared HTTP client and auth header
- [ ] `frontend/exam_intelligence/src/api/apiService.js` — frontend API methods

### Screens and navigation

- [ ] `frontend/exam_intelligence/src/pages/Login.jsx` — sign-in form and token handling
- [ ] `frontend/exam_intelligence/src/pages/Signup.jsx` — account creation form
- [ ] `frontend/exam_intelligence/src/pages/Dashboard.jsx` — document list and controls
- [ ] `frontend/exam_intelligence/src/pages/Chat.jsx` — chat UI, document selection, and sources

## 4. Trace authentication and authorization

- [ ] `backend/app/auth/schemas.py` — signup/login input validation
- [ ] `backend/app/auth/hashing.py` — password hashing and verification
- [ ] `backend/app/auth/jwt_handler.py` — JWT creation and validation
- [ ] `backend/app/auth/dependencies.py` — current-user authentication dependency
- [ ] `backend/app/auth/routes.py` — signup and login workflow
- [ ] `backend/app/db/crud/user.py` — user database helpers
- [ ] `backend/app/db/models/user.py` — user table and relationships

## 5. Understand database setup and data models

### Database setup

- [ ] `backend/app/db/base.py` — SQLAlchemy declarative base
- [ ] `backend/app/db/database.py` — database engine
- [ ] `backend/app/db/session.py` — database sessions and FastAPI dependency
- [ ] `backend/app/db/models/__init__.py` — model imports
- [ ] `backend/create_tables.py` — table creation entry point

### SQLAlchemy models

- [ ] `backend/app/db/models/document.py` — document table and owner/chunk relations
- [ ] `backend/app/db/models/chunk.py` — relational chunk metadata
- [ ] `backend/app/db/models/chat_session.py` — chat session table
- [ ] `backend/app/db/models/message.py` — chat message table

### Database schemas and CRUD

- [ ] `backend/app/db/schemas/user.py` — user request/response schemas
- [ ] `backend/app/db/schemas/document.py` — document request/response schemas
- [ ] `backend/app/db/schemas/chunk.py` — chunk request/response schemas
- [ ] `backend/app/db/schemas/chat.py` — chat session and message schemas
- [ ] `backend/app/db/crud/document.py` — document database operations
- [ ] `backend/app/db/crud/chunk.py` — chunk database operations
- [ ] `backend/app/db/crud/chat.py` — chat persistence helpers

## 6. Trace the PDF ingestion workflow

Follow this path: upload route → ingestion service → PDF parser → text cleaner
and chunker → embeddings → vector database; then inspect relational chunk
metadata persistence.

- [ ] `backend/app/services/__init__.py` — service package
- [ ] `backend/app/api/upload.py` — upload request and ingestion handoff
- [ ] `backend/app/services/ingestion_service.py` — ingestion orchestration
- [ ] `backend/app/rag/parser.py` — PDF text extraction and OCR fallback
- [ ] `backend/app/utils/helpers.py` — text cleanup
- [ ] `backend/app/rag/chunker.py` — page text splitting and chunk metadata
- [ ] `backend/app/rag/embedder.py` — text-to-vector model and embedding methods
- [ ] `backend/app/rag/vectordb.py` — ChromaDB storage and document operations
- [ ] `backend/app/db/crud/chunk.py` — relational chunk record persistence

## 7. Trace the chat and RAG answer workflow

Follow this path: chat page → API client → chat endpoint → chat service →
retrieval → vector and keyword scoring → reranking → prompt → LLM → answer and
citations.

- [ ] `backend/app/models/__init__.py` — API model package
- [ ] `backend/app/models/chat.py` — chat request, response, and source schemas
- [ ] `backend/app/models/query.py` — retrieval query schema
- [ ] `backend/app/models/chunk.py` — chunk data schema
- [ ] `backend/app/models/document.py` — document data schema
- [ ] `backend/app/models/retrieval.py` — retrieval result schemas
- [ ] `backend/app/services/chat_service.py` — chat pipeline orchestration
- [ ] `backend/app/rag/retriever.py` — vector search and retrieval result formatting
- [ ] `backend/app/rag/bm25.py` — keyword relevance scoring
- [ ] `backend/app/rag/hybrid_search.py` — vector/keyword score combination
- [ ] `backend/app/rag/reranker.py` — cross-encoder relevance ranking
- [ ] `backend/app/rag/prompt_builder.py` — grounded prompt construction
- [ ] `backend/app/rag/llm_service.py` — Gemini request and response handling
- [ ] `backend/app/api/chat.py` — authenticated chat endpoint
- [ ] `frontend/exam_intelligence/src/pages/Chat.jsx` — renders answers and citations

## 8. Understand document management end to end

- [ ] `backend/app/db/crud/document.py` — document lookup and record deletion
- [ ] `backend/app/rag/vectordb.py` — vector lookup and deletion
- [ ] `backend/app/api/upload.py` — list, view, chunk, and delete endpoints
- [ ] `frontend/exam_intelligence/src/api/apiService.js` — document API calls
- [ ] `frontend/exam_intelligence/src/pages/Dashboard.jsx` — upload, view, and delete UI

## 9. Review deployment configuration

- [ ] `frontend/exam_intelligence/render.yaml` — frontend deployment settings
- [ ] `frontend/exam_intelligence/package.json` — build and lint commands
- [ ] `backend/runtime.txt` — deployed Python runtime

## Progress notes

- Initial repository map completed.
- The project has a React/Vite frontend and a FastAPI backend with authentication,
  relational persistence, PDF ingestion, ChromaDB retrieval, and Gemini responses.
- A pre-existing worktree edit exists in `backend/app/rag/embedder.py`; preserve it
  and review its changes with the user when that file is studied.
- No walkthrough file has been marked understood yet; begin with section 1.

## Questions and observations to revisit

- [ ] Confirm the intended database engine and required environment variables.
- [ ] Trace whether the document ID selected in the chat UI is actually applied
  to vector search.
- [ ] Compare the configured embedding model with the model actually loaded by
  the embedder, and understand the consequences before changing anything.
- [ ] Verify which document API routes are in use and whether
  `backend/app/api/documents.py` is registered.
