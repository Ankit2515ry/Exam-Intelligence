import os
from pathlib import Path
import socket

import pytest


pytestmark = pytest.mark.unit


def test_test_runtime_cannot_use_production_stores(isolated_runtime):
    from app.config import settings
    from app.db import database
    from tests.conftest import ISOLATION_ROOT
    assert database.engine.dialect.name == "sqlite"
    assert Path(database.engine.url.database).is_relative_to(isolated_runtime.root)
    assert Path(settings.UPLOAD_DIR).is_relative_to(isolated_runtime.root)
    assert os.environ["GOOGLE_API_KEY"] == "test-key-no-network"
    assert Path(os.environ["VECTOR_DB_DIR"]).is_relative_to(ISOLATION_ROOT)
    assert isolated_runtime.collection.count() == 0
    with pytest.raises(RuntimeError, match="Network disabled"):
        socket.create_connection(("example.com", 443))
    with socket.socket() as sock:
        with pytest.raises(RuntimeError, match="Network disabled"):
            sock.connect(("127.0.0.1", 5432))
    with pytest.raises(RuntimeError, match="Network disabled"):
        socket.getaddrinfo("example.com", 443)


def test_password_hash_and_token_validation():
    from app.auth.hashing import hash_password, verify_password
    from app.auth.jwt_handler import create_access_token, verify_token
    from jose import jwt
    from app.auth import jwt_handler
    hashed = hash_password("study-pass")
    assert hashed != "study-pass"
    assert verify_password("study-pass", hashed)
    assert not verify_password("different", hashed)
    assert verify_token(create_access_token({"sub": "student@example.com"})) == "student@example.com"
    assert verify_token("invalid") is None
    expired = jwt.encode({"sub": "student@example.com", "exp": 0}, jwt_handler.SECRET_KEY, algorithm=jwt_handler.ALGORITHM)
    assert verify_token(expired) is None


def test_explicit_evaluation_environment_overrides_regular_dotenv(monkeypatch, tmp_path):
    from app.config.environment import load_application_environment

    evaluation_env = tmp_path / "evaluation.env"
    evaluation_env.write_text(
        "EXAM_INTELLIGENCE_EVALUATION_MODE=true\nDATABASE_URL=postgresql://evaluation-only\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://regular-only")
    monkeypatch.setenv("EVALUATION_ENV_FILE", str(evaluation_env))

    load_application_environment()

    assert os.environ["DATABASE_URL"] == "postgresql://evaluation-only"


def test_chunk_consistency_audit_is_read_only(auth_client, db, isolated_runtime, pdf_bytes):
    from app.db.models.chunk import Chunk
    from scripts.check_chunk_consistency import collect_consistency_report

    response = auth_client.post(
        "/api/upload",
        files={"file": ("study.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    before_sql = db.query(Chunk).count()
    before_vectors = isolated_runtime.collection.count()

    report = collect_consistency_report(db, isolated_runtime.collection)

    assert report["mode"] == "read-only"
    assert report["sql_chunk_count"] == before_sql
    assert report["vector_chunk_count"] == before_vectors
    assert report["matching_id_count"] == before_sql
    assert report["sql_ids_missing_from_chroma"] == []
    assert report["chroma_ids_missing_from_sql"] == []
    assert db.query(Chunk).count() == before_sql
    assert isolated_runtime.collection.count() == before_vectors
