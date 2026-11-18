"""Upload a single verified evaluation PDF using the isolated evaluation environment."""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys

from dotenv import dotenv_values
import httpx
from sqlalchemy import create_engine, text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-path", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-pages", type=int, required=True)
    parser.add_argument("--selection-manifest", required=True)
    parser.add_argument("--evaluation-env", required=True)
    args = parser.parse_args()

    env_path = Path(args.evaluation_env).resolve()
    if not env_path.is_file():
        raise RuntimeError(f"Evaluation environment file not found: {env_path}")

    # Set EVALUATION_ENV_FILE before importing any app modules
    os.environ["EVALUATION_ENV_FILE"] = str(env_path)

    values = {k: v for k, v in dotenv_values(env_path).items() if v is not None}
    if values.get("EXAM_INTELLIGENCE_EVALUATION_MODE") != "true":
        raise RuntimeError("Evaluation environment marker is missing")

    db_url = values.get("DATABASE_URL")
    if not db_url or "exam_intelligence_evaluation" not in db_url:
        raise RuntimeError("DATABASE_URL must target exam_intelligence_evaluation")

    pdf_path = Path(args.pdf_path).resolve()
    if not pdf_path.is_file():
        raise RuntimeError(f"PDF file not found: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()
    if sha256 != args.expected_sha256:
        raise RuntimeError(f"SHA-256 mismatch! Expected {args.expected_sha256}, got {sha256}")

    # Check selection manifest
    manifest_path = Path(args.selection_manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next((f for f in manifest.get("files", []) if f["filename"] == pdf_path.name), None)
    if not entry:
        raise RuntimeError(f"PDF {pdf_path.name} not found in selection manifest")
    if entry.get("index_status") != "pending":
        raise RuntimeError(f"PDF {pdf_path.name} is not pending (status: {entry.get('index_status')})")
    if entry.get("document_uuid") is not None:
        raise RuntimeError(f"PDF {pdf_path.name} already has document_uuid: {entry.get('document_uuid')}")

    # Check database: ensure no document with this filename or hash exists
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            existing = conn.execute(
                text("select id, document_uuid, filename from documents where filename=:name"),
                {"name": pdf_path.name},
            ).fetchone()
            if existing:
                raise RuntimeError(f"Document already exists in database: {existing}")
    finally:
        engine.dispose()

    # Import application after environment is locked
    from app.main import app

    email = values.get("EVALUATION_USER_EMAIL")
    password = values.get("EVALUATION_USER_PASSWORD")
    if not email or not password:
        raise RuntimeError("Evaluation user credentials missing from environment file")

    async def _upload():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://evaluation.local", timeout=600.0) as client:
            # Step 1: Login
            login_resp = await client.post(
                "/auth/auth/login",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if login_resp.status_code != 200:
                raise RuntimeError(f"Login failed: {login_resp.status_code} {login_resp.text}")
            token = login_resp.json().get("access_token")
            if not token:
                raise RuntimeError("No access_token returned by login endpoint")

            # Step 2: Upload PDF
            files = {
                "file": (pdf_path.name, pdf_bytes, "application/pdf")
            }
            headers = {
                "Authorization": f"Bearer {token}"
            }
            upload_resp = await client.post("/api/upload", files=files, headers=headers)
            return upload_resp

    print(f"Beginning upload of {pdf_path.name} ({len(pdf_bytes)} bytes)...")
    resp = asyncio.run(_upload())

    if resp.status_code != 200:
        print(f"ERROR: Upload failed with status {resp.status_code}:\n{resp.text}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    print("Upload successful!")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
