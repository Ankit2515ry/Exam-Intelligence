"""Offline runner that reuses production retrieval, reranking, and optional chat."""

from datetime import datetime, timezone
import csv
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

from app.config import settings
from app.evaluation.dataset import canonical_hash, validate_dataset
from app.evaluation.metrics import (
    abstention_metrics, aggregate_human_scores, aggregate_retrieval,
    citation_validity, retrieval_metrics,
)
from app.rag.reranker import rerank
from app.rag.retriever import retrieve_relevant_chunks
from app.rag.vectordb import get_chunk_by_id
from app.services.chat_service import NO_CONTEXT_ANSWER, chat_with_documents


def _revision():
    configured = os.getenv("GIT_COMMIT_SHA") or os.getenv("RENDER_GIT_COMMIT")
    if configured:
        return configured
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return result.stdout.strip() or None


def _source(chunk):
    return {
        "chunk_id": chunk.metadata.get("chunk_id"),
        "document_id": chunk.metadata.get("document_id"),
        "page": chunk.metadata.get("page"),
        "content": chunk.page_content,
        "score": chunk.metadata.get("score"),
        "rerank_score": chunk.metadata.get("rerank_score"),
    }


def _lookup(chunk_id):
    result = get_chunk_by_id(chunk_id)
    if not result.get("ids"):
        return None
    return {"metadata": result["metadatas"][0], "content": result["documents"][0]}


def run_evaluation(
    records,
    *,
    split_name,
    dataset_version,
    corpus_hash,
    user_id,
    corpus_version="unversioned",
    generate_answers=False,
    retrieve_fn=retrieve_relevant_chunks,
    rerank_fn=rerank,
    answer_fn=chat_with_documents,
    lookup_fn=_lookup,
):
    validate_dataset(records, require_approved=True)
    started = time.perf_counter()
    per_question, errors = [], []
    for record in records:
        item = {
            "question_id": record["question_id"],
            "answerable": record["answerable"],
            "reference_answer": record["expected_answer"],
            "retrieval": None,
            "answer": None,
            "sources": [],
            "citation_validity": None,
            "answer_citation_validity": None,
            "human_scores": {},
        }
        try:
            retrieval_started = time.perf_counter()
            candidates = retrieve_fn(
                question=record["question"], user_id=user_id, top_k=settings.RERANK_TOP_K,
                document_id=record["document_scope_uuid"],
            )
            ranked = rerank_fn(question=record["question"], chunks=candidates)[:5]
            item["retrieval_duration_ms"] = (time.perf_counter() - retrieval_started) * 1000
            item["sources"] = [_source(chunk) for chunk in ranked]
            item["retrieval"] = retrieval_metrics(record, item["sources"])
            item["citation_validity"] = citation_validity(
                item["sources"], lookup_fn, expected_user_id=user_id,
                document_scope_uuid=record["document_scope_uuid"],
            )
            if generate_answers:
                generated = answer_fn(
                    question=record["question"], user_id=user_id,
                    document_id=record["document_scope_uuid"],
                )
                item["answer"] = generated["answer"]
                item["answer_sources"] = generated["sources"]
                item["answer_citation_validity"] = citation_validity(
                    generated["sources"], lookup_fn, expected_user_id=user_id,
                    document_scope_uuid=record["document_scope_uuid"],
                )
        except Exception as exc:
            item["error"] = {"category": type(exc).__name__, "message": str(exc)}
            errors.append({"question_id": record["question_id"], "category": type(exc).__name__})
        per_question.append(item)
    retrieval_items = [item["retrieval"] for item in per_question if item["retrieval"] is not None]
    run = {
        "schema_version": 1,
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": _revision(),
        "dataset_version": dataset_version,
        "dataset_hash": canonical_hash(records),
        "evaluation_split": split_name,
        "corpus_hash": corpus_hash,
        "corpus_version": corpus_version,
        "models": {
            "embedding": "all-MiniLM-L6-v2",
            "reranker": settings.RERANK_MODEL,
            "generator": settings.LLM_MODEL,
        },
        "configuration": {
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "candidate_count": settings.RERANK_TOP_K,
            "final_top_k": 5,
            "fusion": {"vector_weight": 0.7, "bm25_weight": 0.3},
            "answer_generation_enabled": generate_answers,
        },
        "sample_count": len(records),
        "retrieval_metrics": aggregate_retrieval(retrieval_items),
        "answer_quality": aggregate_human_scores(per_question),
        "abstention": abstention_metrics(
            [(record, item["answer"]) for record, item in zip(records, per_question)],
            NO_CONTEXT_ANSWER,
        ),
        "latency": {
            "total_run_ms": (time.perf_counter() - started) * 1000,
            "retrieval_per_question_ms": [item.get("retrieval_duration_ms") for item in per_question],
        },
        "errors": errors,
        "exclusions": {
            "answer_metrics_unavailable": not generate_answers,
            "human_review_required": True,
        },
        "per_question": per_question,
    }
    return run


def write_outputs(run, output_directory):
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "evaluation-results.json"
    csv_path = output / "evaluation-results.csv"
    markdown_path = output / "evaluation-summary.md"
    json_path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        fields = ["question_id", "hit_at_5", "precision_at_5", "recall_at_5", "mrr_at_10", "ndcg_at_5", "citation_validity_rate", "error"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for item in run["per_question"]:
            metrics = item.get("retrieval") or {}
            writer.writerow({
                "question_id": item["question_id"],
                **{key: metrics.get(key) for key in fields[1:6]},
                "citation_validity_rate": (item.get("citation_validity") or {}).get("validity_rate"),
                "error": (item.get("error") or {}).get("category"),
            })
    retrieval = run["retrieval_metrics"]
    lines = [
        "# RAG evaluation summary", "",
        f"Run ID: `{run['run_id']}`", "",
        f"Split: `{run['evaluation_split']}`; samples: {run['sample_count']}; errors: {len(run['errors'])}.", "",
        "| Metric | Value |", "|---|---:|",
    ]
    for key in ("hit_at_5", "precision_at_5", "recall_at_5", "mrr_at_10", "ndcg_at_5"):
        value = retrieval.get(key)
        lines.append(f"| {key} | {'NOT MEASURED' if value is None else f'{value:.4f}'} |")
    lines.extend(["", "Answer correctness, faithfulness, and citation support require human review."])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "markdown": str(markdown_path)}
