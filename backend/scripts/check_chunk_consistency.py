"""Read-only SQL/Chroma chunk consistency audit.

This script never writes, repairs, deletes, or reindexes data. Back up PostgreSQL,
ChromaDB, and uploaded files before any separately approved repair operation.
"""

import json

from app.db.session import SessionLocal
from app.db.models.chunk import Chunk
from app.rag.vectordb import collection


def collect_consistency_report(db, vector_collection):
    sql_rows = db.query(Chunk).all()
    sql_ids = {row.chroma_id for row in sql_rows if row.chroma_id}
    vector_ids = set(vector_collection.get().get("ids") or [])
    return {
        "mode": "read-only",
        "sql_chunk_count": len(sql_rows),
        "vector_chunk_count": len(vector_ids),
        "matching_id_count": len(sql_ids & vector_ids),
        "sql_ids_missing_from_chroma": sorted(sql_ids - vector_ids),
        "chroma_ids_missing_from_sql": sorted(vector_ids - sql_ids),
    }


def main():
    with SessionLocal() as db:
        print(json.dumps(collect_consistency_report(db, collection), indent=2))


if __name__ == "__main__":
    main()
