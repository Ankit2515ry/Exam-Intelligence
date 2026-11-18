"""Read-only PDF inventory and pilot label validation."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import fitz

from app.evaluation.dataset import DatasetValidationError, validate_dataset


class PilotValidationError(ValueError):
    pass


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory_corpus(corpus_directory, corpus_version):
    root = Path(corpus_directory).resolve()
    files = sorted(path for path in root.rglob("*.pdf") if path.is_file())
    if not files:
        raise ValueError("Corpus directory contains no PDFs")
    entries, invalid_files = [], []
    for path in files:
        relative_name = path.relative_to(root).as_posix()
        size_bytes = path.stat().st_size
        sha256 = _sha256(path)
        try:
            with fitz.open(path) as document:
                page_count = document.page_count
                if page_count < 1:
                    raise ValueError("PDF contains no pages")
            entries.append({
                "filename": relative_name,
                "size_bytes": size_bytes,
                "sha256": sha256,
                "physical_page_count": page_count,
                "document_uuid": None,
                "index_status": "pending",
                "index_notes": "",
            })
        except Exception as exc:
            invalid_files.append({
                "filename": relative_name,
                "size_bytes": size_bytes,
                "sha256": sha256,
                "error_type": type(exc).__name__,
                "error": str(exc),
            })
    hashes = {}
    for entry in entries:
        hashes.setdefault(entry["sha256"], []).append(entry["filename"])
    duplicates = [names for names in hashes.values() if len(names) > 1]
    return {
        "schema_version": 1,
        "corpus_version": corpus_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": entries,
        "invalid_files": invalid_files,
        "duplicate_sha256_groups": duplicates,
    }


def write_manifest(manifest, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _normalize(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def validate_pilot(records, manifest, corpus_directory):
    try:
        validate_dataset(records, require_approved=False)
    except DatasetValidationError as exc:
        raise PilotValidationError(str(exc)) from exc
    errors, warnings = [], []
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, list):
        raise PilotValidationError("Manifest must contain a files array")
    if manifest.get("duplicate_sha256_groups"):
        errors.append("Corpus contains duplicate PDF hashes; resolve before indexing")
    by_uuid = {}
    for entry in files:
        uuid_value = entry.get("document_uuid")
        if uuid_value:
            if uuid_value in by_uuid:
                errors.append(f"Document UUID is mapped more than once: {uuid_value}")
            by_uuid[uuid_value] = entry
        elif entry.get("index_status") == "indexed":
            errors.append(f"Indexed file is missing document_uuid: {entry.get('filename')}")
    root = Path(corpus_directory).resolve()
    page_cache = {}
    passage_owners = {}
    for record in records:
        question_id = record["question_id"]
        relevant_docs = set(record["relevant_document_ids"])
        span_docs = {span["document_id"] for span in record["supporting_spans"]}
        span_pages = {span["page"] for span in record["supporting_spans"]}
        if span_docs - relevant_docs:
            errors.append(f"{question_id}: supporting span document missing from relevant_document_ids")
        if span_pages - set(record["relevant_page_numbers"]):
            errors.append(f"{question_id}: supporting span page missing from relevant_page_numbers")
        scope = record["document_scope_uuid"]
        if scope is not None and any(document_id != scope for document_id in relevant_docs):
            errors.append(f"{question_id}: relevant document violates selected document scope")
        for document_id in relevant_docs | span_docs | ({scope} if scope else set()):
            if document_id not in by_uuid:
                errors.append(f"{question_id}: UUID is absent from corpus manifest: {document_id}")
        for span in record["supporting_spans"]:
            entry = by_uuid.get(span["document_id"])
            if entry is None:
                continue
            page = span["page"]
            if page > entry["physical_page_count"]:
                errors.append(f"{question_id}: page {page} exceeds {entry['filename']} page count")
                continue
            key = (entry["filename"], page)
            if key not in page_cache:
                pdf_path = (root / entry["filename"]).resolve()
                if not pdf_path.is_relative_to(root) or not pdf_path.exists():
                    errors.append(f"{question_id}: manifest PDF is missing: {entry['filename']}")
                    continue
                with fitz.open(pdf_path) as document:
                    page_cache[key] = _normalize(document.load_page(page - 1).get_text())
            expected = _normalize(span["text"])
            if expected not in page_cache.get(key, ""):
                message = f"{question_id}: supporting passage not found on {entry['filename']} page {page}"
                (warnings if record["ocr_scanned"] else errors).append(message)
            passage_key = (span["document_id"], page, expected)
            passage_owners.setdefault(passage_key, []).append(question_id)
        if record["reviewer_status"] != "approved":
            warnings.append(f"{question_id}: reviewer_status is {record['reviewer_status']}")
    repeated_passages = [ids for ids in passage_owners.values() if len(ids) > 1]
    if repeated_passages:
        warnings.append(f"Repeated supporting passages require one split group: {repeated_passages}")
    if not 10 <= len(records) <= 15:
        warnings.append(f"Pilot contains {len(records)} records; readiness target is 10–15")
    report = {
        "mode": "pilot",
        "record_count": len(records),
        "approved_count": sum(record["reviewer_status"] == "approved" for record in records),
        "errors": errors,
        "warnings": warnings,
        "ready_for_pilot_run": not errors and 10 <= len(records) <= 15 and all(record["reviewer_status"] == "approved" for record in records),
        "final_100_question_rules_applied": False,
    }
    if errors:
        raise PilotValidationError(json.dumps(report, indent=2))
    return report
