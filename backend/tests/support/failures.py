"""Failure injection at real ingestion boundaries, using synthetic content."""

from unittest.mock import Mock


INGESTION_STAGES = ("parse", "embedding", "vector_write", "sql_first", "sql_second")


def inject_ingestion_failure(monkeypatch, stage):
    from app.services import ingestion_service
    from app.rag import vectordb

    if stage not in INGESTION_STAGES:
        raise ValueError(stage)
    if stage == "parse":
        monkeypatch.setattr(ingestion_service.PDFParser, "parse", Mock(side_effect=RuntimeError(stage)))
        return
    monkeypatch.setattr(ingestion_service.PDFParser, "parse", lambda self: [{
        "page": 1,
        "text": "Database normalization reduces duplicate data in relational tables. " * 12,
    }])
    if stage == "embedding":
        monkeypatch.setattr(vectordb, "generate_embeddings", Mock(side_effect=RuntimeError(stage)))
    elif stage == "vector_write":
        store = ingestion_service.store_chunks

        def accepted_then_failed(chunks):
            store(chunks)
            raise RuntimeError(stage)
        monkeypatch.setattr(ingestion_service, "store_chunks", accepted_then_failed)
    else:
        create = ingestion_service.create_chunk
        calls = 0

        def fail_sql(**kwargs):
            nonlocal calls
            calls += 1
            if stage == "sql_first" or calls == 2:
                raise RuntimeError(stage)
            return create(**kwargs)
        monkeypatch.setattr(ingestion_service, "create_chunk", fail_sql)


def ingestion_artifacts(db, runtime):
    from app.db.models.document import Document
    from app.db.models.chunk import Chunk
    return {
        "documents": db.query(Document).count(),
        "sql_chunks": db.query(Chunk).count(),
        "vector_chunks": runtime.collection.count(),
        "pdf_files": len(list((runtime.root / "uploads").rglob("*.pdf"))),
    }
