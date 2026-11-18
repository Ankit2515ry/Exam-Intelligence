"""
Inspect actual indexed chunks in ChromaDB for cited document pages.
"""
import os
import sys
from pathlib import Path
from dotenv import dotenv_values
import chromadb

backend_dir = Path("backend").resolve()
env_vals = dotenv_values(backend_dir / "evaluation" / "private" / "evaluation-corpus-v1.env")
chroma_path = env_vals["VECTOR_DB_DIR"]

client = chromadb.PersistentClient(path=chroma_path)
col = client.get_collection("exam_intelligence")

# Cited documents:
# 10 RAG: cbd60b93-0e2b-4e19-b8ad-d63461eac601
# DBMS: f513d63e-e487-4d83-b40a-af81169662de
# OS: 6c04513a-30bd-4fea-814c-9f07c1e9c0b7

rag_id = "cbd60b93-0e2b-4e19-b8ad-d63461eac601"
dbms_id = "f513d63e-e487-4d83-b40a-af81169662de"
os_id = "6c04513a-30bd-4fea-814c-9f07c1e9c0b7"

def show_chunks(doc_id, page):
    res = col.get(where={"$and": [{"document_id": doc_id}, {"page": page}]}, include=["documents", "metadatas"])
    print(f"\n=== Doc {doc_id[:8]}... Page {page} ({len(res['ids'])} chunks) ===")
    for cid, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
        print(f"  [Chunk {meta.get('chunk_index')}] (len={len(doc)}): {repr(doc)}")

if __name__ == "__main__":
    show_chunks(rag_id, 1)
    show_chunks(rag_id, 3)
    show_chunks(rag_id, 4)
    show_chunks(rag_id, 7)
    show_chunks(rag_id, 8)
    show_chunks(dbms_id, 2)
    show_chunks(dbms_id, 5)
    show_chunks(dbms_id, 8)
    show_chunks(os_id, 6)
    show_chunks(os_id, 7)
    show_chunks(os_id, 9)
    show_chunks(os_id, 10)
    show_chunks(os_id, 11)
