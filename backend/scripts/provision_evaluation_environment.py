"""Provision only the approved isolated evaluation resources.

This script never alters the regular application database, default Chroma directory,
or default uploads. Its private environment file is intentionally gitignored.
"""

import json
import os
from pathlib import Path
import secrets
import sys

from dotenv import dotenv_values, set_key
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


DATABASE_NAME = "exam_intelligence_evaluation"
EVALUATION_EMAIL = "evaluation-corpus-v1@local.invalid"


def main():
    backend_root = Path(__file__).resolve().parents[1]
    regular_env = backend_root / ".env"
    private_root = backend_root / "evaluation" / "private"
    evaluation_env = private_root / "evaluation-corpus-v1.env"
    source_url = dotenv_values(regular_env).get("DATABASE_URL")
    if not source_url:
        raise RuntimeError("Regular DATABASE_URL is required only to create the new evaluation database")
    source = make_url(source_url)
    if source.database == DATABASE_NAME:
        raise RuntimeError("Refusing to provision from the evaluation database")
    evaluation_url = source.set(database=DATABASE_NAME)

    maintenance_url = source.set(database="postgres")
    maintenance_engine = create_engine(maintenance_url)
    created_database = False
    try:
        with maintenance_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            exists = connection.execute(
                text("select exists(select 1 from pg_database where datname=:name)"),
                {"name": DATABASE_NAME},
            ).scalar_one()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{DATABASE_NAME}"'))
                created_database = True
    finally:
        maintenance_engine.dispose()

    vector_directory = (private_root / "chroma-corpus-v1").resolve()
    upload_directory = (private_root / "uploads-corpus-v1").resolve()
    chunks_directory = (private_root / "chunks-corpus-v1").resolve()
    for directory in (vector_directory, upload_directory, chunks_directory):
        directory.mkdir(parents=True, exist_ok=True)

    if evaluation_env.exists():
        values = dotenv_values(evaluation_env)
        if values.get("EXAM_INTELLIGENCE_EVALUATION_MODE") != "true":
            raise RuntimeError("Refusing to overwrite a non-evaluation private environment file")
    else:
        evaluation_env.parent.mkdir(parents=True, exist_ok=True)
        evaluation_env.touch()

    password = secrets.token_urlsafe(32)
    configuration = {
        "EXAM_INTELLIGENCE_EVALUATION_MODE": "true",
        "DATABASE_URL": evaluation_url.render_as_string(hide_password=False),
        "VECTOR_DB_DIR": str(vector_directory),
        "UPLOAD_DIR": str(upload_directory),
        "CHUNKS_DIR": str(chunks_directory),
        "EVALUATION_USER_EMAIL": EVALUATION_EMAIL,
        "EVALUATION_USER_PASSWORD": password,
        "SECRET_KEY": secrets.token_urlsafe(48),
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "GOOGLE_API_KEY": "disabled-for-evaluation-no-provider",
        "PERFORMANCE_METRICS_ENABLED": "false",
    }
    for key, value in configuration.items():
        set_key(evaluation_env, key, value, quote_mode="auto")

    os.environ["EVALUATION_ENV_FILE"] = str(evaluation_env)
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.db.models.user import User
    from app.db.models.document import Document  # noqa: F401
    from app.db.models.chunk import Chunk  # noqa: F401
    from app.db.models.chat_session import ChatSession  # noqa: F401
    from app.db.models.message import Message  # noqa: F401
    from app.auth.hashing import hash_password

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        account = db.query(User).filter(User.email == EVALUATION_EMAIL).first()
        created_user = False
        if account is None:
            account = User(
                name="Evaluation Corpus User",
                email=EVALUATION_EMAIL,
                hashed_password=hash_password(password),
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            created_user = True
        set_key(evaluation_env, "EVALUATION_USER_ID", str(account.id), quote_mode="auto")
        owner_count = db.query(Document).filter(Document.uploaded_by == account.id).count()
        verified_user = db.query(User).filter(User.id == account.id, User.email == EVALUATION_EMAIL).one()
    engine.dispose()

    print(json.dumps({
        "database": DATABASE_NAME,
        "database_created": created_database,
        "evaluation_environment_file": str(evaluation_env),
        "vector_directory": str(vector_directory),
        "upload_directory": str(upload_directory),
        "chunks_directory": str(chunks_directory),
        "evaluation_user_id": verified_user.id,
        "evaluation_user_email": "configured_redacted",
        "evaluation_user_created": created_user,
        "evaluation_user_document_count": owner_count,
        "credentials": "redacted",
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"provisioned": False, "error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        raise
