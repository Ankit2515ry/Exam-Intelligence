# Exam Intelligence development progress

Updated: 2026-11-17. The root `PROJECT_PROGRESS.md` remains the earlier learning
checklist. This file tracks implementation phases and verified deliverables.

## Phase 1: testing foundation, baseline, architecture

- [x] Review the three original health tests and document their limits.
- [x] Add pytest discovery, markers, test dependencies and full-source coverage configuration.
- [x] Install pre-import isolation: no `.env`, live stores, model downloads or outbound services.
- [x] Use per-test temporary SQL files, real in-memory Chroma and synthetic PDFs.
- [x] Add unit and real-app HTTP tests for authentication, ownership and document lifecycle.
- [x] Add strict regressions for all six requested bug categories.
- [x] Exercise five ingestion failure stages and partial deletion after directory cleanup fails.
- [x] Record synthetic scope, candidate-count, parser/chunker and artifact metrics in JSON.
- [x] List unavailable quality/performance/deployment measurements with reasons.
- [x] Write current-architecture HLD and LLD, separating proposed repairs.
- [x] Document the frontend lint failure before editing the effect.
- [x] Repair only Dashboard's initial request effect; verify lint and build.
- [x] Preserve the RAG algorithm, business-logic defects and existing upload.py edit.

The Phase 1 suite contained 58 cases: 46 passing and 12 strict expected failures.
See [BASELINE_REPORT.md](BASELINE_REPORT.md) for the preserved Phase 1 snapshot and
the current Phase 2A comparison.

## Files delivered

New testing files:

- `backend/.coveragerc`
- `backend/pytest.ini`
- `backend/requirements-test.txt`
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `backend/tests/unit/test_rag.py`
- `backend/tests/unit/test_safety_and_auth.py`
- `backend/tests/integration/test_api.py`
- `backend/tests/integration/test_health_dependencies.py`
- `backend/tests/regression/test_known_bugs.py`
- `backend/tests/evaluation/test_baseline.py`
- `backend/tests/support/__init__.py`
- `backend/tests/support/doubles.py`
- `backend/tests/support/corpus.py`
- `backend/tests/support/failures.py`
- `backend/tests/support/known_bugs.py`

New documentation/evidence:

- `docs/HLD.md`
- `docs/LLD.md`
- `docs/PROJECT_PROGRESS.md`
- `docs/BASELINE_REPORT.md`
- `docs/TESTING_STRATEGY.md`
- `docs/baseline_results.json`

Modified existing files:

- `backend/.gitignore`: ignore generated coverage/test evidence.
- `frontend/exam_intelligence/src/pages/Dashboard.jsx`: scoped lint repair.
- `README.md`: documentation links and pytest instructions.
- `PROJECT_PROGRESS.md`: pointer to this phase tracker; old learning checklist retained.

Generated local evidence/build output is ignored: `backend/.coverage`,
`backend/tests/artifacts/`, and the frontend's
`node_modules/.cache/phase1-build/`. Test dependencies were installed only into
the existing backend virtual environment. `backend/requirements.txt` is unchanged.

The pre-existing `backend/app/api/upload.py` trailing-whitespace worktree change
is preserved. No backend application-source file was edited in Phase 1.

## Phase 2A: document-specific retrieval and chat correctness

- [x] Send `document_uuid` from the chat selector instead of the SQL integer ID.
- [x] Validate selected IDs as canonical UUIDv4 values.
- [x] Verify the selected document exists and belongs to the authenticated user.
- [x] Apply both user ID and document UUID in document-scoped Chroma queries.
- [x] Preserve user-only filtering for global-scope queries.
- [x] Build the grounded prompt once when context exists.
- [x] Return the existing response contract without calling Gemini when retrieval is empty.
- [x] Return HTTP 404 for missing chunks while preserving existing ownership validation.
- [x] Convert only BUG-01 through BUG-04 strict xfails into normal regressions.
- [x] Regenerate the synthetic baseline and run backend, frontend lint, and frontend build checks.

Phase 2A modified these application files:

- `backend/app/models/chat.py`
- `backend/app/api/chat.py`
- `backend/app/rag/vectordb.py`
- `backend/app/services/chat_service.py`
- `frontend/exam_intelligence/src/pages/Chat.jsx`

It also updated:

- `backend/tests/regression/test_known_bugs.py`
- `backend/tests/integration/test_api.py`
- `backend/tests/evaluation/test_baseline.py`
- `docs/PROJECT_PROGRESS.md`
- `docs/BASELINE_REPORT.md`
- `docs/HLD.md`
- `docs/LLD.md`
- `docs/baseline_results.json`

Final Phase 2A verification: **55 passed, 7 strict expected failures, 0 failed,
0 errors, and 1 warning**. Displayed coverage remains **82%**. Frontend lint and
production build pass. Five former xfails now pass normally; three new guards
cover global-scope retrieval, selected-document ownership, and the HTTP no-context path.

Synthetic document isolation changed from 2 requested-document matches among 4
returned chunks (0.50 scope precision) to 2 among 2 (1.00). The other-user fraction
remained 0.00. Prompt construction changed from five calls to one for the five-
context fixture. These values are controlled fixture measurements, not production
accuracy.

## Phase 2B: PDF upload security, validation, and OCR portability

- [x] Enforce a configurable byte limit while streaming rather than buffering the upload.
- [x] Validate the PDF signature and parse every page before creating a database record.
- [x] Reject empty, malformed/corrupt, encrypted, MIME-mismatched, and oversized PDFs.
- [x] Treat the client filename as display metadata only and reject path/absolute-name input.
- [x] Store new PDFs at a server-generated `<UPLOAD_DIR>/<document UUID>/document.pdf` path.
- [x] Remove staged files and directories when pre-database validation fails.
- [x] Configure Tesseract with `TESSERACT_CMD`, otherwise resolve `tesseract` through `PATH`.
- [x] Keep text PDFs independent of OCR and emit a clear OCR error only when OCR is required.
- [x] Close PyMuPDF documents, pixmaps, byte streams, PIL images, and uploaded streams.
- [x] Add isolated synthetic upload/OCR tests and rerun all Phase 2A regressions.

Phase 2B application and test files:

- `backend/app/config/settings.py`
- `backend/app/api/upload.py`
- `backend/app/rag/parser.py`
- `backend/tests/conftest.py`
- `backend/tests/integration/test_upload_security.py` (new)
- `backend/tests/unit/test_rag.py`

Documentation/evidence updated: `docs/HLD.md`, `docs/LLD.md`,
`docs/BASELINE_REPORT.md`, this file, and `docs/baseline_results.json`.

Final verification: **70 passed, 7 strict expected failures, 0 failed, 0 errors,
and 1 warning**. Displayed coverage is **83%**. Frontend lint and production build
pass. These are isolated synthetic tests; no production files, PostgreSQL,
persistent Chroma, Gemini, or real Tesseract process was accessed.

## Remaining work: awaiting approval

- [ ] Persist actual Chroma chunk IDs in SQL.
- [ ] Design rollback/compensation for failed uploads and recoverable deletion; avoid per-chunk partial commits.
- [ ] Agree on a representative evaluation corpus and real-model measurement protocol.
- [ ] Consider ranking/chunking/prompt changes only after obtaining that quality baseline.

No Phase 2C code, schema migration, ranking change, new user-facing functionality,
production operation or deployment is included. Work stops here pending review.
