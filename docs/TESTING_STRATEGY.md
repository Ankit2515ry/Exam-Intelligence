# Phase 1 testing strategy

Status: implemented, 2026-11-17. No business-logic or RAG repairs are part of this
phase. The single application-source repair is the documented Dashboard lint fix.

## Existing health tests: review and limitations

`backend/tests/test_health.py` is retained unchanged. Its three unittest cases
verify: liveness does not call dependency checks; healthy mocked dependencies
produce ready/200; a mocked SQL failure produces not_ready/503 while the vector
check still runs and the failure is logged.

They mount only the health router on a small FastAPI object. Consequently they
do not prove that `app.main` starts or registers the routes. Mocking the check
functions also bypasses actual `SELECT 1`, Chroma `count`, database configuration,
connection failures and persistence. They do not cover vector-only failure, both
dependencies failing, recovery, authentication, ownership, PDF handling, chat,
cleanup, actual Gemini/OCR health, timeouts, or deployment networking.

The expanded integration suite mounts the actual app, executes successful health
probes against isolated real SQL/Chroma, and adds vector-only/both failures and
recovery. Dependency failures are still injected in-process; this is not a live
PostgreSQL or networking availability test.

## Structure and boundaries

```text
backend/
  requirements-test.txt          pytest and pytest-cov only
  pytest.ini                    discovery, markers, strict marker handling
  .coveragerc                   includes unimported namespace-package files
  tests/
    conftest.py                 pre-import isolation and per-test resources
    test_health.py              original three unittest cases, unchanged
    unit/
      test_rag.py               parsing, chunking, scores, embeddings, prompt, LLM errors
      test_safety_and_auth.py   isolation guards, password/JWT behavior
    integration/
      test_api.py               actual FastAPI routes, authentication, ownership, lifecycle
      test_health_dependencies.py
    regression/
      test_known_bugs.py        strict expected failures, BUG-01 through BUG-06D
    evaluation/
      test_baseline.py          deterministic synthetic measurements
    support/
      doubles.py               external model substitutes
      corpus.py                synthetic document/chunk membership labels
      failures.py              ingestion boundary faults and artifact inventory
      known_bugs.py            specific violated-invariant exception
    artifacts/                 ignored generated coverage and JUnit evidence
```

Markers are `unit`, `integration`, `regression`, and `evaluation`. Tests use real
application functions rather than copying or AST-extracting their implementations.
Unit-marked cases still share the safe application bootstrap; the marker indicates
what is asserted, not that resource fixtures are absent.

## Isolation guarantees and limitations

`conftest.py` installs safety controls before any application module is imported:

1. It refuses a process where the app/config/database already loaded, rather than
   assuming it can undo import-time side effects.
2. It overrides all app storage paths, SQL URL, JWT settings and Gemini key with
   test values, and disables `dotenv.load_dotenv` so local secrets are not loaded.
3. It replaces external SentenceTransformer, CrossEncoder and Gemini library
   constructors with deterministic doubles before model construction.
4. It intercepts `chromadb.PersistentClient` and returns a real in-memory
   `EphemeralClient`, refusing non-sandbox paths. The actual Chroma collection,
   vector matching, metadata filters and deletion remain in use.
5. It blocks TCP connects, direct localhost connects, DNS resolution and UDP
   `sendto`. Windows' standard-library `socketpair` is allowed only during its
   internal self-pipe construction, which asyncio needs; arbitrary localhost
   service connections remain forbidden.
6. Each case gets a fresh SQLite file under pytest's temporary directory, a new
   Chroma collection, temporary uploads/chunks directories and a fresh LLM double.
   SQL foreign-key enforcement is enabled. Sessions close, engines dispose,
   dependency overrides clear, and the collection is deleted after each case.

The SQL tests validate real ORM operations and commit ordering but do not establish
PostgreSQL-specific constraints, isolation levels, driver behavior, migrations or
performance. In-memory Chroma does not prove disk persistence, restart recovery or
multi-worker locking. Real OCR execution and model semantic inference are outside
this offline suite. The safety guards are a test harness, not a general security
sandbox for arbitrary untrusted code.

Most protected-route tests override the current-user dependency with a fixture
user; separate signup/login/bearer tests exercise the actual authentication flow.
Synthetic PDFs are generated in memory. No production corpus is read or cleaned up.

## Known bugs and expected failures

Strict xfails assert desired future behavior while retaining the current bugs.
They are not skipped tests: each body executes. `strict=True` makes an unexpected
pass fail the run. Most accept only the dedicated `KnownDefect` assertion; an
unrelated setup error or ordinary assertion failure remains a real failure. The
empty/missing-result unit cases expect their specific observed exception types.

| ID | Test case | Current reproduction |
|---|---|---|
| BUG-01 | `test_document_specific_search_excludes_other_documents` | Same-user passages from a different UUID appear |
| BUG-02 | `test_numeric_document_id_is_rejected_at_uuid_contract` | A numeric string is accepted and forwarded, rather than rejected by a canonical UUID boundary |
| BUG-03 | `test_empty_retrieval_returns_a_response_without_crashing` | `UnboundLocalError` |
| BUG-04 | `test_missing_chunk_lookup_returns_empty_results` | `IndexError` |
| BUG-04 | `test_missing_chunk_api_returns_404` | HTTP 500 rather than 404 |
| BUG-05 | `test_sql_chunk_ids_match_chroma_ids` | Generated SQL references differ from vector IDs |
| BUG-06 | `test_failed_ingestion_removes_all_created_artifacts[parse]` | Document row and file survive |
| BUG-06 | `...[embedding]` | Document row and file survive |
| BUG-06 | `...[vector_write]` | Accepted vectors, document and file survive |
| BUG-06 | `...[sql_first]` | Vectors, document and file survive |
| BUG-06 | `...[sql_second]` | One committed SQL chunk plus vectors, document and file survive |
| BUG-06D | `test_cleanup_failure_preserves_consistent_document_state` | Nonempty-directory failure leaves SQL after file/vectors were deleted |

The numeric-ID test replays the current UI payload into the real backend route;
the dropdown's `doc.id` use is a source observation, not a browser automation
result. UUID validation is a proposed repair contract. The direct SQL/Chroma
consistency test uses the actual ingestion service and CRUD with SQLite.

Failure injections raise at parser/embedding boundaries, after an accepted vector
write, or before the first/second SQL chunk helper call. They demonstrate missing
compensation for these precise faults; they do not prove behavior for every
database crash, filesystem failure or process interruption.

Baseline characterization tests intentionally assert current observed counts.
When Phase 2 repairs land, update those counts from new measurements, and remove
only the xfail markers for the corresponding approved fixes. Do not delete the
regressions or silently mark unexpected failures as expected.

## Commands

Use a fresh process from `backend/` with application dependencies already
installed. This phase added only the following test dependencies to the existing
virtual environment:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-test.txt
.\venv\Scripts\python.exe -B -m pytest -q
```

The authoritative baseline command is:

```powershell
.\venv\Scripts\python.exe -B -m pytest -q --tb=short --cov=app --cov-branch --cov-report=term-missing --cov-report=json:tests/artifacts/coverage.json --junitxml=tests/artifacts/junit.xml --baseline-output=../docs/baseline_results.json
```

Useful focused runs:

```powershell
.\venv\Scripts\python.exe -B -m pytest -m regression -q
.\venv\Scripts\python.exe -B -m pytest -m regression --runxfail -q --tb=line
.\venv\Scripts\python.exe -B -m pytest -m evaluation -q
```

The `--runxfail` command deliberately exits nonzero while the defects remain; it
exposes the actual failures rather than treating them as expected. Do not use it
as the normal green-suite command. A `--baseline-output` report generated by a
filtered run contains only that run's measurements/outcomes; use the full command
for the committed baseline.

From `frontend/exam_intelligence/`:

```powershell
npm.cmd run lint
npm.cmd run build -- --outDir node_modules/.cache/phase1-build
```

The alternate output directory verifies compilation without replacing the existing
`dist/`. No frontend test framework, Docker service, CI provider or hosted resource
was introduced. Lint/build do not verify browser interaction; initial-load, upload
refresh, delete refresh and stale-response UI behavior still need browser checks.

## Coverage interpretation and future evaluation

Coverage counts application source, including unimported namespace directories,
without excluding unused schemas/CRUD. Expected-failure paths and model-double
paths contribute to execution coverage. No arbitrary coverage threshold was set
before establishing the baseline. Coverage cannot establish semantic accuracy,
correctness of broken paths, production availability, or model performance.

The checked-in JSON captures actual installed package versions, test outcomes and
synthetic measurements. No elapsed model timing is reported from mocked calls.
For real retrieval quality, first agree on a versioned, permitted document corpus,
questions, relevance judgments, expected answers and citation labels. For latency,
specify hardware, model/cache versions, warm/cold protocol, network conditions,
load and percentiles. Run those future evaluations against separate permitted
test resources; production data is not a default benchmark source.
