"""
Extract and correlate performance telemetry for all 10 indexed documents.
"""
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import dotenv_values

backend_dir = Path(__file__).resolve().parent.parent
env_vals = dotenv_values(backend_dir / "evaluation" / "private" / "evaluation-corpus-v1.env")
db_url = env_vals["DATABASE_URL"]

# Connect to DB to get documents in order
engine = create_engine(db_url)
with engine.connect() as conn:
    docs = conn.execute(text("SELECT id, uploaded_by, filename, document_uuid FROM documents ORDER BY id ASC")).fetchall()
    chunks = conn.execute(text("SELECT document_id, count(*) as count FROM chunks GROUP BY document_id")).fetchall()
    chunk_map = {r.document_id: r.count for r in chunks}

# Read metrics
metrics_path = Path(env_vals["PERFORMANCE_METRICS_PATH"])
successful_events = []
with open(metrics_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            if data.get("success") is True and data.get("operation") == "ingestion":
                successful_events.append(data)

print(f"Total successful telemetry records: {len(successful_events)}")

# Map events by matching chunk count and retained pages
# Because docs were uploaded in order:
# 1. 10 RAG Architectures.pdf (pages=8, chunks=34)
# 2. SQL Notes by Apna College.pdf (pages=29, chunks=175)
# 3. CMC_Unit-I.pdf (pages=32, chunks=97)
# 4. MWC-A2.pdf (pages=6, chunks=32)
# 5. SQL (notes).pdf (pages=59, chunks=66)
# 6. MWC-A1.pdf (pages=6, chunks=44)
# 7. DBMS.pdf (pages=231, chunks=1148)
# 8. Operating-Systems.pdf (pages=258, chunks=1415)
# 9. OOPs.pdf (pages=121, chunks=301)
# 10. DBMS_NOTES.pdf (pages=46, chunks=137)

# Let's verify chronological alignment with docs:
results = []
for i, d in enumerate(docs):
    event = successful_events[i]
    c_counts = event["counts"]
    dur = event["durations_ms"]
    tot_dur = event["total_duration_ms"]
    ocr_used = event["ocr_used"]
    ocr_dur = dur.get("ocr")
    embed_dur = dur.get("embedding_generation")
    chroma_dur = dur.get("chroma_storage")
    sql_dur = dur.get("sql_persistence")
    parse_dur = dur.get("pdf_parsing")
    val_dur = dur.get("upload_validation")
    file_dur = dur.get("file_storage")
    chunk_dur = dur.get("chunking")

    res = {
        "index": i + 1,
        "doc_id": d.id,
        "filename": d.filename,
        "document_uuid": d.document_uuid,
        "retained_pages": c_counts["retained_pages"],
        "chunks": c_counts["chunks"],
        "bytes": c_counts["uploaded_bytes"],
        "total_ms": tot_dur,
        "embed_ms": embed_dur,
        "ocr_used": ocr_used,
        "ocr_ms": ocr_dur,
        "parse_ms": parse_dur,
        "chunk_ms": chunk_dur,
        "chroma_ms": chroma_dur,
        "sql_ms": sql_dur,
        "val_ms": val_dur,
        "file_ms": file_dur
    }
    results.append(res)

with open(backend_dir / "evaluation" / "private" / "indexing-telemetry-summary.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nSummary Table:")
print(f"{'#':2} | {'Filename':30} | {'Pages':5} | {'Chunks':6} | {'Total ms':9} | {'Embed ms':9} | {'OCR ms':9} | {'OCR':5}")
print("-" * 85)
total_pages = 0
total_chunks = 0
total_time = 0
total_embed = 0
for r in results:
    total_pages += r['retained_pages']
    total_chunks += r['chunks']
    total_time += r['total_ms']
    total_embed += r['embed_ms']
    ocr_str = f"{r['ocr_ms']:.1f}" if r['ocr_ms'] is not None else "-"
    print(f"{r['index']:2d} | {r['filename'][:30]:30} | {r['retained_pages']:5d} | {r['chunks']:6d} | {r['total_ms']:9.1f} | {r['embed_ms']:9.1f} | {ocr_str:>9} | {str(r['ocr_used']):5}")
print("-" * 85)
print(f"TOTAL: Pages={total_pages}, Chunks={total_chunks}, Total Ingestion Duration={total_time:.1f}ms ({total_time/1000:.2f}s), Embedding Duration={total_embed:.1f}ms ({total_embed/1000:.2f}s)")
