"""Deterministic retrieval, citation, abstention, and human-score metrics."""

import math
import re
from statistics import mean


def _normalize(text):
    return " ".join(re.sub(r"\s+", " ", (text or "").lower()).split())


def _deduplicate(results):
    seen, unique = set(), []
    for result in results:
        key = result.get("chunk_id") or (
            result.get("document_id"), result.get("page"), _normalize(result.get("content"))
        )
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return unique


def relevant_units(record):
    spans = record.get("supporting_spans") or []
    if spans:
        return [
            (span["document_id"], int(span["page"]), _normalize(span["text"]), float(span.get("relevance_grade", 1)))
            for span in spans
        ]
    return [(document_id, int(page), "", 1.0) for document_id in record.get("relevant_document_ids", []) for page in record.get("relevant_page_numbers", [])]


def result_relevance(result, units):
    document_id, page, content = result.get("document_id"), result.get("page"), _normalize(result.get("content"))
    matched = []
    for index, (unit_doc, unit_page, span, grade) in enumerate(units):
        if document_id == unit_doc and page == unit_page and (not span or span in content or content in span):
            matched.append((index, grade))
    return matched


def retrieval_metrics(record, results, k=5, mrr_k=10):
    results = _deduplicate(results)
    units = relevant_units(record)
    if not units:
        return {"eligible": False, "hit_at_5": None, "precision_at_5": None, "recall_at_5": None, "mrr_at_10": None, "ndcg_at_5": None}
    top = results[:k]
    matches = [result_relevance(result, units) for result in top]
    relevant_result_count = sum(bool(item) for item in matches)
    covered = {index for item in matches for index, _ in item}
    reciprocal = 0.0
    for rank, result in enumerate(results[:mrr_k], 1):
        if result_relevance(result, units):
            reciprocal = 1 / rank
            break
    gains = [max((grade for _, grade in item), default=0.0) for item in matches]
    dcg = sum((2 ** gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = sorted((grade for *_, grade in units), reverse=True)[:k]
    idcg = sum((2 ** gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(ideal, 1))
    return {
        "eligible": True,
        "hit_at_5": 1.0 if relevant_result_count else 0.0,
        "precision_at_5": relevant_result_count / k,
        "recall_at_5": len(covered) / len(units),
        "mrr_at_10": reciprocal,
        "ndcg_at_5": dcg / idcg if idcg else None,
    }


def aggregate_retrieval(per_question):
    eligible = [item for item in per_question if item.get("eligible")]
    output = {"eligible_questions": len(eligible), "excluded_no_relevance_labels": len(per_question) - len(eligible)}
    for key in ("hit_at_5", "precision_at_5", "recall_at_5", "mrr_at_10", "ndcg_at_5"):
        values = [item[key] for item in eligible if item.get(key) is not None]
        output[key] = mean(values) if values else None
    return output


def citation_validity(sources, lookup, expected_user_id=None, document_scope_uuid=None):
    valid, errors = 0, []
    for source in sources:
        chunk_id = source.get("chunk_id")
        stored = lookup(chunk_id) if chunk_id else None
        if not stored:
            errors.append({"chunk_id": chunk_id, "error": "missing_chunk"})
            continue
        metadata = stored.get("metadata", {})
        if metadata.get("document_id") != source.get("document_id") or metadata.get("page") != source.get("page"):
            errors.append({"chunk_id": chunk_id, "error": "metadata_mismatch"})
            continue
        if document_scope_uuid and source.get("document_id") != document_scope_uuid:
            errors.append({"chunk_id": chunk_id, "error": "scope_violation"})
            continue
        if expected_user_id is not None and metadata.get("user_id") != expected_user_id:
            errors.append({"chunk_id": chunk_id, "error": "user_isolation_violation"})
            continue
        valid += 1
    return {"returned": len(sources), "valid": valid, "invalid": len(errors), "validity_rate": valid / len(sources) if sources else None, "errors": errors}


def abstention_metrics(records_and_answers, abstention_text):
    correct, false, missed, eligible = 0, 0, 0, 0
    for record, answer in records_and_answers:
        if answer is None:
            continue
        eligible += 1
        abstained = answer.strip() == abstention_text.strip()
        if not record["answerable"] and abstained:
            correct += 1
        elif record["answerable"] and abstained:
            false += 1
        elif not record["answerable"] and not abstained:
            missed += 1
    return {"eligible": eligible, "correct_abstentions": correct, "false_abstentions": false, "missed_abstentions": missed}


def aggregate_human_scores(results):
    keys = ("factual_correctness", "faithfulness", "citation_support")
    output = {}
    for key in keys:
        values = [item.get("human_scores", {}).get(key) for item in results]
        values = [float(value) for value in values if value in (0, 0.5, 1)]
        output[key] = {"reviewed": len(values), "mean": mean(values) if values else None}
    return output
