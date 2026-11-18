"""Install isolation BEFORE application imports, including collection-time imports.

No project .env is loaded, no production database is opened, and no model is
downloaded. Only external model libraries and Chroma's persistent constructor
are replaced; application modules, SQL CRUD, and Chroma query logic remain real.
"""

import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket
import sys
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import uuid
from unittest.mock import patch

import pytest

from tests.support.doubles import (
    FakeCrossEncoder,
    FakeGenerativeModel,
    FakeSentenceTransformer,
)


if any(name in sys.modules for name in ("app.main", "app.config.settings", "app.db.database")):
    raise RuntimeError("Start a fresh pytest process: application imported before isolation")

_sandbox = tempfile.TemporaryDirectory(prefix="exam-intelligence-tests-")
ISOLATION_ROOT = Path(_sandbox.name).resolve()
_patches = []


def _start(patcher):
    _patches.append(patcher)
    return patcher.start()


_start(patch.dict(os.environ, {
    "DATABASE_URL": f"sqlite:///{(ISOLATION_ROOT / 'bootstrap.sqlite').as_posix()}",
    "UPLOAD_DIR": str(ISOLATION_ROOT / "uploads"),
    "CHUNKS_DIR": str(ISOLATION_ROOT / "chunks"),
    "VECTOR_DB_DIR": str(ISOLATION_ROOT / "vectors"),
    "MAX_PDF_UPLOAD_SIZE_BYTES": str(1024 * 1024),
    "TESSERACT_CMD": "",
    "SECRET_KEY": "isolated-tests-only-not-a-production-secret",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
    "GOOGLE_API_KEY": "test-key-no-network",
    "PERFORMANCE_METRICS_ENABLED": "false",
    "PERFORMANCE_PROVIDER_MODE": "mocked",
    "PERFORMANCE_MEASUREMENT_CLASS": "synthetic",
}))
_start(patch("dotenv.load_dotenv", return_value=False))
_start(patch("socket.create_connection", side_effect=RuntimeError("Network disabled in tests")))
_start(patch("socket.getaddrinfo", side_effect=RuntimeError("Network disabled in tests")))
_start(patch("socket.gethostbyname", side_effect=RuntimeError("Network disabled in tests")))
_start(patch("socket.gethostbyname_ex", side_effect=RuntimeError("Network disabled in tests")))
_start(patch("socket.socket.sendto", side_effect=RuntimeError("Network disabled in tests")))
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_socketpair = socket.socketpair
_socket_context = threading.local()


def _guard_connect(sock, address):
    if getattr(_socket_context, "inside_socketpair", False):
        return _original_connect(sock, address)
    raise RuntimeError("Network disabled in tests")


def _guard_connect_ex(sock, address):
    if getattr(_socket_context, "inside_socketpair", False):
        return _original_connect_ex(sock, address)
    raise RuntimeError("Network disabled in tests")


def _internal_socketpair(*args, **kwargs):
    # Windows implements the event-loop self-pipe with a loopback socketpair.
    # Only this stdlib operation may connect; arbitrary localhost is still denied.
    previous = getattr(_socket_context, "inside_socketpair", False)
    _socket_context.inside_socketpair = True
    try:
        return _original_socketpair(*args, **kwargs)
    finally:
        _socket_context.inside_socketpair = previous


_start(patch("socket.socket.connect", new=_guard_connect))
_start(patch("socket.socket.connect_ex", new=_guard_connect_ex))
_start(patch("socket.socketpair", new=_internal_socketpair))

_sentence_transformers = ModuleType("sentence_transformers")
_sentence_transformers.SentenceTransformer = FakeSentenceTransformer
_sentence_transformers.CrossEncoder = FakeCrossEncoder
_genai = ModuleType("google.generativeai")
_genai.configure = lambda **kwargs: None
_genai.GenerativeModel = FakeGenerativeModel
_start(patch.dict(sys.modules, {
    "sentence_transformers": _sentence_transformers,
    "google.generativeai": _genai,
}))

import google  # noqa: E402
import chromadb  # noqa: E402
from chromadb.config import Settings  # noqa: E402

_start(patch.object(google, "generativeai", _genai, create=True))
_chroma_client = chromadb.EphemeralClient(
    settings=Settings(anonymized_telemetry=False, allow_reset=True)
)


def _ephemeral_only(path, **kwargs):
    if not Path(path).resolve().is_relative_to(ISOLATION_ROOT):
        raise RuntimeError("Refusing Chroma construction outside test sandbox")
    return _chroma_client


_start(patch.object(chromadb, "PersistentClient", side_effect=_ephemeral_only))


def pytest_addoption(parser):
    parser.addoption("--baseline-output", help="Write synthetic measurements as JSON to this path")


def pytest_configure(config):
    config._baseline_measurements = {}


def pytest_sessionfinish(session, exitstatus):
    output = session.config.getoption("--baseline-output")
    if output:
        terminal = session.config.pluginmanager.get_plugin("terminalreporter")
        report = {
            "schema_version": 1,
            "scope": "Synthetic offline fixtures; not production quality or performance",
            "python": platform.python_version(),
            "packages": {name: importlib.metadata.version(name) for name in (
                "pytest", "pytest-cov", "coverage", "fastapi", "httpx", "SQLAlchemy",
                "chromadb", "langchain-text-splitters", "rank-bm25", "PyMuPDF",
            )},
            "exit_status": int(exitstatus),
            "test_outcomes": {key: len(terminal.stats.get(key, [])) for key in (
                "passed", "failed", "error", "xfailed", "xpassed", "skipped",
            )},
            "warning_count": len(terminal.stats.get("warnings", [])),
            "measurements": session.config._baseline_measurements,
        }
        path = Path(output).resolve()
        # Baseline output must be inside this checkout, never an arbitrary path.
        if not path.is_relative_to(Path(__file__).resolve().parents[2]):
            raise RuntimeError("Baseline output must be inside the project workspace")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def pytest_unconfigure(config):
    for patcher in reversed(_patches):
        patcher.stop()
    _sandbox.cleanup()


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from app.db import database, session
    from app.db.base import Base
    import app.db.models  # noqa: F401
    from app.config import settings
    from app.rag import vectordb, llm_service

    engine = create_engine(f"sqlite:///{(tmp_path / 'test.sqlite').as_posix()}")

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(session, "engine", engine)
    monkeypatch.setattr(session, "SessionLocal", factory)
    Base.metadata.create_all(engine)

    for name, directory in (("UPLOAD_DIR", "uploads"), ("CHUNKS_DIR", "chunks"),
                            ("VECTOR_DB_DIR", "vectors")):
        path = tmp_path / directory
        path.mkdir()
        monkeypatch.setattr(settings, name, str(path))

    collection = _chroma_client.create_collection(name=f"test-{uuid.uuid4().hex}")
    monkeypatch.setattr(vectordb, "collection", collection)
    monkeypatch.setattr(llm_service, "model", FakeGenerativeModel())

    from app.api import upload
    monkeypatch.setattr(upload, "UPLOAD_DIR", settings.UPLOAD_DIR)
    monkeypatch.setattr(upload, "CHUNKS_DIR", settings.CHUNKS_DIR)
    monkeypatch.setattr(
        upload,
        "MAX_PDF_UPLOAD_SIZE_BYTES",
        settings.MAX_PDF_UPLOAD_SIZE_BYTES,
    )
    from app.main import app
    app.dependency_overrides.clear()
    runtime = SimpleNamespace(engine=engine, session_factory=factory,
                              collection=collection, app=app, root=tmp_path)
    yield runtime
    app.dependency_overrides.clear()
    _chroma_client.delete_collection(collection.name)
    engine.dispose()


@pytest.fixture
def db(isolated_runtime):
    with isolated_runtime.session_factory() as session:
        yield session


@pytest.fixture
def client(isolated_runtime):
    from fastapi.testclient import TestClient
    with TestClient(isolated_runtime.app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def user_factory(db):
    from app.db.models.user import User

    def create(email="student@example.com", hashed_password="unused-test-hash"):
        user = User(name="Test Student", email=email, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    return create


@pytest.fixture
def user(user_factory):
    return user_factory()


@pytest.fixture
def auth_client(client, isolated_runtime, user):
    from app.auth.dependencies import get_current_user
    isolated_runtime.app.dependency_overrides[get_current_user] = lambda: user
    return client


@pytest.fixture
def document_factory(db, isolated_runtime):
    from app.db.crud.document import create_document

    def create(owner_id, document_uuid=None):
        document_uuid = document_uuid or str(uuid.uuid4())
        path = isolated_runtime.root / "uploads" / document_uuid / "study.pdf"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"%PDF-1.4 synthetic fixture; not used for parsing")
        return create_document(db, "Study", "study.pdf", str(path), "General", owner_id, document_uuid)
    return create


@pytest.fixture
def pdf_bytes():
    import fitz
    with fitz.open() as document:
        page = document.new_page()
        text = "Database normalization organizes relational tables and reduces redundant data. " * 8
        remaining = page.insert_textbox(fitz.Rect(72, 72, 500, 700), text, fontsize=11)
        assert remaining >= 0, "Synthetic PDF text must fit on the page"
        return document.tobytes()


@pytest.fixture
def record_baseline(request):
    def record(name, values):
        request.config._baseline_measurements[name] = values
    return record
