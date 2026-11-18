"""Sequentially index and verify the nine pending evaluation corpus PDFs."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from dotenv import dotenv_values
import httpx
from sqlalchemy import create_engine, text
import chromadb


def main():
    backend_root = Path(__file__).resolve().parents[1]
    evaluation_env = backend_root / "evaluation" / "private" / "evaluation-corpus-v1.env"
    selection_path = backend_root / "evaluation" / "private" / "corpus-v1-selection.json"
    manifest_path = backend_root / "evaluation" / "private" / "corpus-v1-manifest.json"
    corpus_dir = backend_root / "evaluation" / "corpus" / "corpus-v1"
    metrics_path = backend_root / "evaluation" / "private" / "metrics-corpus-v1.jsonl"
    regular_env = backend_root / ".env"

    if not evaluation_env.is_file():
        raise RuntimeError(f"Evaluation env file missing: {evaluation_env}")
    os.environ["EVALUATION_ENV_FILE"] = str(evaluation_env)

    from app.config.environment import load_application_environment
    load_application_environment()

    from scripts.evaluation_preflight import collect_preflight_report
    from app.main import app
    from app.rag.vectordb import search_chunks

    values = {k: v for k, v in dotenv_values(evaluation_env).items() if v is not None}
    db_url = values.get("DATABASE_URL")
    vector_dir = values.get("VECTOR_DB_DIR")
    upload_dir = values.get("UPLOAD_DIR")
    email = values.get("EVALUATION_USER_EMAIL")
    password = values.get("EVALUATION_USER_PASSWORD")
    user_id = int(values.get("EVALUATION_USER_ID", "1"))

    # Initial Preflight
    print("=" * 80)
    print("RUNNING INITIAL PREFLIGHT")
    print("=" * 80)
    preflight = collect_preflight_report(
        evaluation_env=str(evaluation_env),
        mode="full",
        verify_regular_env=str(regular_env),
        backend_root=backend_root,
    )
    if not preflight["ready"]:
        print(json.dumps(preflight, indent=2))
        raise RuntimeError("Initial preflight failed! Aborting before any write.")
    print(f"Initial preflight PASSED. Current document count: {preflight['evaluation_account']['document_count']}")

    # Load selection manifest and sort pending files
    selection_data = json.loads(selection_path.read_text(encoding="utf-8"))
    pending_files = [f for f in selection_data["files"] if f.get("index_status") == "pending"]
    pending_sorted = sorted(pending_files, key=lambda x: x["size_bytes"])

    print(f"Found {len(pending_sorted)} pending PDFs to index.")
    for idx, p in enumerate(pending_sorted, 1):
        print(f"  [{idx}/{len(pending_sorted)}] {p['filename']} ({p['size_bytes']:,} bytes, {p['physical_page_count']} pages)")

    engine = create_engine(db_url)
    chroma_client = chromadb.PersistentClient(path=vector_dir)
    collection = chroma_client.get_collection("exam_intelligence")

    async def _upload_pdf(pdf_filename, pdf_bytes):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://evaluation.local", timeout=900.0) as client:
            login_resp = await client.post(
                "/auth/auth/login",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if login_resp.status_code != 200:
                raise RuntimeError(f"Login failed: {login_resp.status_code} {login_resp.text}")
            token = login_resp.json().get("access_token")
            if not token:
                raise RuntimeError("Missing access token")

            files = {"file": (pdf_filename, pdf_bytes, "application/pdf")}
            headers = {"Authorization": f"Bearer {token}"}
            upload_resp = await client.post("/api/upload", files=files, headers=headers)
            return upload_resp

    overall_start = time.perf_counter()
    TIME_BUDGET_SEC = 28 * 60  # 28 minutes safety limit
    completed_reports = []

    for idx, file_info in enumerate(pending_sorted, 1):
        filename = file_info["filename"]
        expected_bytes = file_info["size_bytes"]
        expected_sha = file_info["sha256"]
        physical_pages = file_info["physical_page_count"]

        elapsed_total = time.perf_counter() - overall_start
        if elapsed_total > TIME_BUDGET_SEC:
            print(f"TIME BUDGET REACHED ({elapsed_total:.1f}s elapsed). Stopping cleanly before {filename}.")
            break

        print("\n" + "=" * 80)
        print(f"INDEXING [{idx}/{len(pending_sorted)}]: {filename}")
        print("=" * 80)

        # 1. Verify file on disk
        pdf_path = corpus_dir / filename
        if not pdf_path.is_file():
            raise RuntimeError(f"Corpus file missing: {pdf_path}")
        pdf_bytes = pdf_path.read_bytes()
        actual_sha = hashlib.sha256(pdf_bytes).hexdigest()
        if len(pdf_bytes) != expected_bytes or actual_sha != expected_sha:
            raise RuntimeError(f"Corpus file corrupted or modified: {filename} (got {actual_sha}, expected {expected_sha})")

        # 2. Verify absence from SQL
        with engine.connect() as conn:
            existing = conn.execute(
                text("select id, document_uuid from documents where filename=:name"),
                {"name": filename},
            ).fetchone()
            if existing:
                raise RuntimeError(f"Document already exists in evaluation DB: {existing}")

        # 3. Track metrics line count before upload
        initial_metrics_lines = 0
        if metrics_path.exists():
            initial_metrics_lines = len(metrics_path.read_text(encoding="utf-8").strip().splitlines())

        # 4. Upload PDF
        step_start = time.perf_counter()
        resp = asyncio.run(_upload_pdf(filename, pdf_bytes))
        step_elapsed = time.perf_counter() - step_start

        if resp.status_code != 200:
            print(f"CRITICAL: Upload failed for {filename} with status {resp.status_code}: {resp.text}")
            sys.exit(1)

        upload_data = resp.json()
        doc_payload = upload_data.get("document", {})
        doc_uuid = doc_payload.get("document_uuid")
        sql_id = doc_payload.get("id")
        retained_pages = doc_payload.get("total_pages")
        chunk_count = doc_payload.get("total_chunks")

        if not doc_uuid or not sql_id:
            raise RuntimeError(f"Malformed upload response: {upload_data}")

        print(f"  Upload response: HTTP 200, doc_uuid={doc_uuid}, sql_id={sql_id}, pages={retained_pages}, chunks={chunk_count}")

        # 5. Verify SQL record
        with engine.connect() as conn:
            sql_doc = conn.execute(
                text("select id, document_uuid, filename, file_path, uploaded_by from documents where document_uuid=:u"),
                {"u": doc_uuid},
            ).mappings().one()
            sql_chunks = conn.execute(
                text("select id, chunk_index, page_number, chroma_id, content from chunks where document_id=:d order by chunk_index"),
                {"d": sql_id},
            ).mappings().all()

        if sql_doc["uploaded_by"] != user_id:
            raise RuntimeError(f"Owner mismatch in SQL: {sql_doc['uploaded_by']} != {user_id}")
        if sql_doc["filename"] != filename:
            raise RuntimeError(f"Filename mismatch in SQL: {sql_doc['filename']} != {filename}")

        stored_file_path = Path(sql_doc["file_path"])
        if not stored_file_path.is_file():
            raise RuntimeError(f"Stored file missing: {stored_file_path}")
        if not stored_file_path.resolve().is_relative_to(Path(upload_dir).resolve()):
            raise RuntimeError(f"Stored file not in upload_dir: {stored_file_path}")
        stored_sha = hashlib.sha256(stored_file_path.read_bytes()).hexdigest()
        if stored_sha != expected_sha:
            raise RuntimeError(f"Stored file SHA mismatch: {stored_sha} != {expected_sha}")

        if len(sql_chunks) != chunk_count:
            raise RuntimeError(f"SQL chunk count mismatch: {len(sql_chunks)} != {chunk_count}")

        # 6. Verify Chroma collection
        chroma_res = collection.get(where={"document_id": doc_uuid}, include=["metadatas", "documents"])
        chroma_ids = set(chroma_res["ids"])
        sql_chroma_ids = set(c["chroma_id"] for c in sql_chunks)

        if chroma_ids != sql_chroma_ids:
            diff1 = sql_chroma_ids - chroma_ids
            diff2 = chroma_ids - sql_chroma_ids
            raise RuntimeError(f"Chroma vs SQL ID mismatch! Missing in Chroma: {diff1}, Extra in Chroma: {diff2}")

        if len(chroma_res["metadatas"]) != chunk_count:
            raise RuntimeError(f"Chroma metadata count mismatch: {len(chroma_res['metadatas'])} != {chunk_count}")

        for meta in chroma_res["metadatas"]:
            if meta["user_id"] != user_id:
                raise RuntimeError(f"Chroma user_id mismatch: {meta['user_id']}")
            if meta["document_id"] != doc_uuid:
                raise RuntimeError(f"Chroma document_id mismatch: {meta['document_id']}")
            if not (1 <= meta["page"] <= physical_pages):
                raise RuntimeError(f"Chroma page out of bounds: page {meta['page']} (physical={physical_pages})")

        for doc_text in chroma_res["documents"]:
            if not doc_text or not doc_text.strip():
                raise RuntimeError("Chroma document contains empty chunk content")

        # 7. Scoped probe check
        probe_res = search_chunks(
            query="database query test",
            user_id=user_id,
            top_k=min(5, chunk_count),
            document_id=doc_uuid,
        )
        for meta in probe_res["metadatas"][0]:
            if meta["document_id"] != doc_uuid or meta["user_id"] != user_id:
                raise RuntimeError(f"Chroma probe leaked foreign document/user: {meta}")

        # 8. Read telemetry from metrics-corpus-v1.jsonl
        telemetry = None
        if metrics_path.exists():
            new_lines = metrics_path.read_text(encoding="utf-8").strip().splitlines()
            if len(new_lines) > initial_metrics_lines:
                last_event = json.loads(new_lines[-1])
                if last_event.get("operation") == "ingestion":
                    telemetry = last_event

        ingestion_dur_ms = telemetry["total_duration_ms"] if telemetry else step_elapsed * 1000
        durations_ms = telemetry["durations_ms"] if telemetry else {}
        embedding_dur_ms = durations_ms.get("embedding_generation")
        ocr_dur_ms = durations_ms.get("ocr")
        ocr_used = telemetry.get("ocr_used", False) if telemetry else False

        # 9. Update selection manifest
        for item in selection_data["files"]:
            if item["filename"] == filename:
                item["document_uuid"] = doc_uuid
                item["index_status"] = "indexed"
                item["retained_pages"] = retained_pages
                item["total_chunks"] = chunk_count
                break
        selection_path.write_text(json.dumps(selection_data, indent=2) + "\n", encoding="utf-8")

        # 10. Update inventory manifest
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest_data["files"]:
            if item["filename"] == filename:
                item["document_uuid"] = doc_uuid
                item["index_status"] = "indexed"
                item["index_notes"] = f"Phase 4C Step 2 indexed ({chunk_count} chunks)"
                break
        manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

        # 11. Run operational preflight
        post_preflight = collect_preflight_report(
            evaluation_env=str(evaluation_env),
            mode="full",
            verify_regular_env=str(regular_env),
            backend_root=backend_root,
        )
        if not post_preflight["ready"]:
            raise RuntimeError(f"Post-upload preflight failed for {filename}!")

        report_item = {
            "index": idx,
            "filename": filename,
            "document_uuid": doc_uuid,
            "physical_pages": physical_pages,
            "retained_pages": retained_pages,
            "total_chunks": chunk_count,
            "total_duration_ms": ingestion_dur_ms,
            "embedding_duration_ms": embedding_dur_ms,
            "ocr_used": ocr_used,
            "ocr_duration_ms": ocr_dur_ms,
            "sql_chroma_id_match": True,
            "status": "verified",
        }
        completed_reports.append(report_item)
        print(f"VERIFIED {filename}: UUID={doc_uuid}, pages={retained_pages}/{physical_pages}, chunks={chunk_count}, duration={ingestion_dur_ms:.1f}ms, preflight=PASS (doc_count={post_preflight['evaluation_account']['document_count']})")

    print("\n" + "=" * 80)
    print("PHASE 4C STEP 2 BATCH EXECUTION FINISHED")
    print("=" * 80)
    print(json.dumps(completed_reports, indent=2))


if __name__ == "__main__":
    main()
