# Gold evaluation dataset

Phase 4 defines the schema and workflow but does not contain a fabricated gold
dataset. `backend/evaluation/dataset.template.json` intentionally has zero records.

## Target composition

The approved dataset should contain exactly 100 human-reviewed questions:

| Category | Count |
|---|---:|
| Direct factual | 45 |
| Paraphrased/semantic | 20 |
| Multi-step reasoning | 10 |
| Unanswerable from the corpus | 15 |
| Cross-document isolation/conflict | 10 |

OCR/scanned and mathematical flags are independent metadata, not extra categories.

Each record contains a stable question ID, question, selected document UUID or
null global scope, expected answer, answerability, relevant documents/pages,
verbatim supporting spans, category, OCR/math flags, reviewer state, and notes.
Supporting spans use document UUID plus one-based PDF page and text. This is the
ground-truth relevance unit, so chunks may change without relabeling the source.

Answerable records require an expected answer and at least one supporting span.
Unanswerable records have a null/empty expected answer and no invented evidence.
Only `approved` records may be executed by the runner.

## Human labeling procedure

1. Give each PDF a stable corpus document UUID and record its SHA-256 hash.
2. A labeler reads the PDF, writes the question independently of retrieved output,
   and copies the shortest sufficient supporting span with its visible PDF page.
3. The labeler writes a concise reference answer containing only supported facts.
4. A second reviewer checks answerability, scope, page, span, answer, and category.
5. Disagreements remain `in_review`; only resolved records become `approved`.
6. Unanswerable questions must be checked across their declared scope.
7. Do not inspect held-out results while tuning future retrieval settings.

Human answer review uses separate dimensions:

- Factual correctness: 1 correct, 0.5 partly correct, 0 incorrect.
- Faithfulness: 1 all claims supported, 0.5 mixed support, 0 unsupported.
- Citation support: 1 citations support the answer, 0.5 partial, 0 unsupported.

Correctness and faithfulness are deliberately not interchangeable. Deterministic
citation validity only proves that an ID/page/document exists and respects scope;
it does not prove that a citation supports an answer.

## Validation and splitting

Validation rejects missing labels, invalid categories, duplicate IDs, exact or
near-duplicate questions, invalid spans, and unapproved execution records.

The default seed is `20261118`. Splits are 20 development, 30 validation, and 50
held-out. Document groups are kept together when exact capacities allow; forced
group splits are listed in split metadata. Metadata includes dataset SHA-256,
split hashes, IDs, seed, sizes, and the held-out non-tuning policy.

```powershell
cd backend
.\venv\Scripts\python.exe -m scripts.rag_evaluation evaluation/private/gold-v1.json --validate
.\venv\Scripts\python.exe -m scripts.rag_evaluation evaluation/private/gold-v1.json --split-output evaluation/private/splits-v1
```

Private PDFs, labels, and result directories are gitignored.

## Phase 4B corpus inventory

Place only approved copies under `backend/evaluation/corpus/corpus-v1/`. Do not
move or delete application uploads. Create a local manifest before indexing:

```powershell
cd C:\Users\ankit\Desktop\Exam_Intelligence\backend
New-Item -ItemType Directory -Force evaluation\corpus\corpus-v1 | Out-Null
.\venv\Scripts\python.exe -m scripts.rag_evaluation `
  --inventory-corpus evaluation\corpus\corpus-v1 `
  --corpus-version corpus-v1 `
  --manifest-output evaluation\private\corpus-v1-manifest.json
```

The read-only inventory records relative filename, bytes, SHA-256, physical page
count, pending index status, and a blank document UUID. Identical SHA-256 groups
must be resolved before upload so the same PDF is not indexed twice.

Create a separate evaluation account and configure isolated SQL, Chroma, and
upload directories. Upload each manifest entry exactly once through the existing
API/UI. After each successful upload, copy the returned `document_uuid` into that
manifest entry and change `index_status` to `indexed`. Compare `/api/documents`
filename/UUID pairs with the manifest. For `/api/chunks/{uuid}`, confirm every
page is between 1 and `physical_page_count` and visually verify several source
pages against the PDF. Never point this procedure at production stores.

## Pilot dataset

Copy `backend/evaluation/pilot.template.json` to the ignored path
`backend/evaluation/private/pilot-v1.json`. Keep 10–15 records. Pilot validation
uses the same required record fields as the final dataset but does not require
100 records, category quotas, or a held-out split. Final splitting rules remain
unchanged.

The following is an **illustrative shape only**, not approved ground truth and not
intended to be pasted unchanged:

```json
{
  "question_id": "pilot-001",
  "question": "<human-written question from an approved PDF>",
  "document_scope_uuid": "<UUID copied from the isolated upload response>",
  "expected_answer": "<human-verified reference answer>",
  "answerable": true,
  "relevant_document_ids": ["<same approved PDF UUID>"],
  "relevant_page_numbers": [1],
  "supporting_spans": [{
    "document_id": "<same approved PDF UUID>",
    "page": 1,
    "text": "<exact passage copied from that physical PDF page>"
  }],
  "category": "direct_factual",
  "ocr_scanned": false,
  "mathematical": false,
  "reviewer_status": "draft",
  "reviewer_notes": "<review notes>"
}
```

Pilot validation checks structure, UUID presence in the manifest, page bounds,
span/document/page consistency, extractable passage text, duplicates, conflicting
scope, repeated supporting passages, and approval counts. For scanned pages where
PyMuPDF cannot find text, passage checking becomes a manual-review warning.

```powershell
.\venv\Scripts\python.exe -m scripts.rag_evaluation `
  evaluation\private\pilot-v1.json --pilot `
  --manifest evaluation\private\corpus-v1-manifest.json `
  --corpus-dir evaluation\corpus\corpus-v1
```

An approved 10–15 record pilot can be run retrieval-only with:

```powershell
.\venv\Scripts\python.exe -m scripts.rag_evaluation `
  evaluation\private\pilot-v1.json --pilot --run-pilot `
  --manifest evaluation\private\corpus-v1-manifest.json `
  --corpus-version corpus-v1 `
  --corpus-dir evaluation\corpus\corpus-v1 `
  --user-id <isolated-evaluation-user-id> `
  --output evaluation\results\pilot-v1
```

Phase 4B explicitly prohibits `--generate-answers`; the pilot run makes no Gemini call.

## Isolated evaluation startup

The private file `evaluation/private/evaluation-corpus-v1.env` is created only by
the approved provisioning command and is gitignored. Every evaluation invocation
must name it explicitly. Do not rely on the regular `.env`.

```powershell
$envFile = (Resolve-Path evaluation\private\evaluation-corpus-v1.env).Path
.\venv\Scripts\python.exe -B -m scripts.evaluation_preflight `
  --evaluation-env $envFile --mode infrastructure --require-ready
.\venv\Scripts\python.exe -B -m scripts.evaluation_preflight `
  --evaluation-env $envFile --mode full --verify-regular-env .env --require-ready
```

Infrastructure mode is safe before schema/account bootstrap. Full mode additionally
requires the dedicated evaluation account, schema, zero owned documents, nondefault
Chroma/uploads, and absence of that account from the regular database. It exits
nonzero if any check fails. Set `EVALUATION_ENV_FILE` to this private file before
launching the backend; the application loader uses it with override precedence and
requires the evaluation-mode marker, preventing regular `.env` resource fallback.

Provisioning is a separately approved, one-time action. The provisioner creates
only `exam_intelligence_evaluation`, the three approved private directories, the
application schema, and the dedicated account; it refuses to use the evaluation DB
as its source database and never resets or migrates `exam_intelligence`.
