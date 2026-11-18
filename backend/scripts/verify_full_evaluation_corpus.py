"""
Comprehensive verification of the full evaluation corpus (10 documents)
Validates SQL, Chroma, File system, Manifests, and Metrics.
"""
import json
import os
import sys
from pathlib import Path
import chromadb
from dotenv import dotenv_values
from sqlalchemy import create_engine, text

def main():
    backend_dir = Path(__file__).resolve().parent.parent
    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))

    env_vals = dotenv_values(backend_dir / "evaluation" / "private" / "evaluation-corpus-v1.env")
    for k, v in env_vals.items():
        if v is not None:
            os.environ[k] = str(v)

    db_url = os.environ.get("DATABASE_URL")
    chroma_path = os.environ.get("VECTOR_DB_DIR")
    upload_path = os.environ.get("UPLOAD_DIR")
    chunks_path = os.environ.get("CHUNKS_DIR")

    print(f"Connected DB: {db_url}")
    print(f"Chroma Path: {chroma_path}")
    print(f"Upload Path: {upload_path}")
    print(f"Chunks Path: {chunks_path}")

    # 1. Manifest verification
    sel_path = backend_dir / "evaluation" / "private" / "corpus-v1-selection.json"
    with open(sel_path, "r", encoding="utf-8") as f:
        selection_data = json.load(f)

    selected_files = selection_data.get("files", [])
    print(f"\nManifest Selected Files: {len(selected_files)}")
    for i, sf in enumerate(selected_files, 1):
        print(f"  [{i:2d}] {sf['filename']}: status={sf.get('index_status')} uuid={sf.get('document_uuid')} pages={sf.get('retained_pages', sf.get('physical_page_count'))}/{sf.get('physical_page_count')} chunks={sf.get('total_chunks')}")

    # 2. SQL DB verification
    engine = create_engine(db_url)
    with engine.connect() as conn:
        docs = conn.execute(text("SELECT id, uploaded_by, filename, document_uuid FROM documents ORDER BY id ASC")).fetchall()
        print(f"\nSQL Documents Count: {len(docs)}")
        doc_map = {}
        for d in docs:
            print(f"  SQL Doc ID={d.id:2d}: user={d.uploaded_by} file={d.filename} uuid={d.document_uuid}")
            doc_map[d.document_uuid] = d

        chunks = conn.execute(text("SELECT id, document_id, chunk_index, page_number, chroma_id FROM chunks ORDER BY id ASC")).fetchall()
        print(f"\nSQL Chunks Count: {len(chunks)}")

        sql_chroma_ids = {c.chroma_id for c in chunks}
        
        # Per document chunk counts
        doc_chunk_counts = conn.execute(text("SELECT document_id, count(*) as count FROM chunks GROUP BY document_id")).fetchall()
        doc_chunk_map = {r.document_id: r.count for r in doc_chunk_counts}

    # 3. Chroma verification
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name="exam_intelligence")
    chroma_count = collection.count()
    print(f"\nChroma Collection Count: {chroma_count}")

    chroma_all = collection.get(include=["metadatas"])
    chroma_ids = set(chroma_all["ids"])
    print(f"Chroma Unique Vector IDs: {len(chroma_ids)}")

    # 4. Consistency Checks
    assert len(docs) == 10, f"Expected 10 documents, found {len(docs)}"
    for d in docs:
        assert d.uploaded_by == 1, f"Expected uploaded_by=1, found {d.uploaded_by} for doc {d.id}"

    assert len(chunks) == chroma_count, f"SQL chunk count ({len(chunks)}) != Chroma count ({chroma_count})"
    assert sql_chroma_ids == chroma_ids, f"Mismatch between SQL chroma_ids and Chroma vector IDs! Diff: {sql_chroma_ids ^ chroma_ids}"

    # 5. Manifest vs SQL mapping
    total_manifest_pages = 0
    total_manifest_chunks = 0
    for sf in selected_files:
        assert sf.get("index_status") == "indexed", f"Manifest file {sf['filename']} not marked indexed"
        uuid = sf.get("document_uuid")
        assert uuid in doc_map, f"UUID {uuid} from manifest not found in SQL"
        sql_doc = doc_map[uuid]
        sql_chunks_for_doc = doc_chunk_map.get(sql_doc.id, 0)
        expected_chunks = sf.get("total_chunks")
        if expected_chunks is not None:
            assert expected_chunks == sql_chunks_for_doc, f"Chunk count mismatch for {sf['filename']}: manifest={expected_chunks}, sql={sql_chunks_for_doc}"
        total_manifest_pages += sf.get("retained_pages", sf.get("physical_page_count", 0))
        total_manifest_chunks += sql_chunks_for_doc

    print(f"\nTotal Retained Pages across corpus: {total_manifest_pages}")
    print(f"Total Chunks across corpus: {total_manifest_chunks}")

    # 6. Metrics parsing
    metrics_path = Path(os.environ.get("PERFORMANCE_METRICS_PATH"))
    events = []
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    print(f"\nTelemetry events found: {len(events)}")
    for ev in events:
        total_dur = ev.get("duration_ms")
        dur_str = f"{total_dur:.1f}" if isinstance(total_dur, (int, float)) else str(total_dur)
        print(f"  Telemetry: {ev.get('filename')}: doc_uuid={ev.get('document_uuid')} pages={ev.get('pages')} chunks={ev.get('chunks')} total_dur={dur_str}ms embed_dur={ev.get('embedding_duration_ms')}ms ocr={ev.get('ocr_used')} ocr_dur={ev.get('ocr_duration_ms')}")

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
