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

The measured suite currently contains 58 cases: 46 passing and 12 strict expected
failures. See [BASELINE_REPORT.md](BASELINE_REPORT.md) for authoritative execution
results, coverage, measured values and limitations. Expected failures mean the
business defects remain; they do not mean Phase 2 has been implemented.

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

## Phase 2: recommendations, awaiting approval

- [ ] Fix UI selection and API UUID validation together; apply owner plus UUID filters.
- [ ] Handle empty retrieval and missing chunks explicitly, including HTTP contracts.
- [ ] Persist actual Chroma chunk IDs in SQL.
- [ ] Design rollback/compensation for failed uploads and recoverable deletion; avoid per-chunk partial commits.
- [ ] Remove the fixed bugs' strict xfails and remeasure characterization baselines.
- [ ] Agree on a representative evaluation corpus and real-model measurement protocol.
- [ ] Consider ranking/chunking/prompt changes only after obtaining that quality baseline.

No Phase 2 code, schema migration, ranking change, new user-facing functionality,
production operation or deployment is authorized by Phase 1. Work stops here
pending approval for the next phase.
