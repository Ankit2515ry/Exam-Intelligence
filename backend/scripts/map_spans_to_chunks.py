"""
Map verified supporting passages for Q01-Q15 to indexed chunks in ChromaDB.
"""
import json
import re
from pathlib import Path
from dotenv import dotenv_values
import chromadb

def _normalize(text):
    return " ".join(re.sub(r"\s+", " ", (text or "").lower()).split())

backend_dir = Path("backend").resolve()
env_vals = dotenv_values(backend_dir / "evaluation" / "private" / "evaluation-corpus-v1.env")
client = chromadb.PersistentClient(path=env_vals["VECTOR_DB_DIR"])
col = client.get_collection("exam_intelligence")

pilot_path = backend_dir / "evaluation" / "private" / "pilot-v1.json"
records = json.loads(pilot_path.read_text(encoding="utf-8"))["records"]

print(f"{'QID':4} | {'Doc UUID':8} | {'Pg':3} | {'Mapped Chunks (chunk_index, chunk_id)':50}")
print("-" * 80)

mapping_results = []
for r in records:
    qid = r["question_id"]
    doc_id = r["document_scope_uuid"]
    spans = r["supporting_spans"]
    
    # Get all chunks for this doc
    chunks = col.get(where={"document_id": doc_id}, include=["documents", "metadatas"])
    
    span_matches = []
    for s_idx, span in enumerate(spans):
        page = span["page"]
        norm_span = _normalize(span["text"])
        
        matched_chunks = []
        for cid, content, meta in zip(chunks["ids"], chunks["documents"], chunks["metadatas"]):
            if meta.get("page") == page:
                norm_content = _normalize(content)
                if norm_span in norm_content or norm_content in norm_span:
                    matched_chunks.append({
                        "chunk_index": meta.get("chunk_index"),
                        "chunk_id": cid,
                        "match_type": "span_in_chunk" if norm_span in norm_content else "chunk_in_span"
                    })
        span_matches.append({
            "span_index": s_idx,
            "page": page,
            "matched_chunks": matched_chunks
        })
    
    all_matched = [f"c{c['chunk_index']} ({c['chunk_id'][:8]}...)" for sm in span_matches for c in sm["matched_chunks"]]
    print(f"{qid:4} | {doc_id[:8]} | {','.join(str(p) for p in r['relevant_page_numbers']):3} | {', '.join(all_matched)}")
    
    mapping_results.append({
        "question_id": qid,
        "document_scope_uuid": doc_id,
        "span_matches": span_matches
    })

out_path = backend_dir / "evaluation" / "private" / "chunk_mapping_results.json"
out_path.write_text(json.dumps(mapping_results, indent=2), encoding="utf-8")
print(f"\nWrote chunk mapping to {out_path}")
