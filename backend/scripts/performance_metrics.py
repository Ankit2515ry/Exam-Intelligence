"""Validate, export, and summarize privacy-safe performance JSONL events."""

import argparse
import csv
from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import mean

REQUIRED = {
    "schema_version", "request_id", "timestamp", "operation", "durations_ms",
    "total_duration_ms", "success", "provider_mode", "measurement_class",
}


def load_events(path):
    events, malformed = [], []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                event = json.loads(line)
                if not isinstance(event, dict) or not REQUIRED.issubset(event):
                    raise ValueError("missing required fields")
                if event["operation"] not in {"chat", "ingestion"}:
                    raise ValueError("unsupported operation")
                events.append(event)
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                malformed.append({"line": line_number, "error": str(exc)})
    return events, malformed


def percentile(values, percent):
    """Nearest-rank percentile: sorted value at ceil(p/100*n), one-based."""
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    return ordered[max(0, math.ceil(percent / 100 * len(ordered)) - 1)]


def latency_stats(values):
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return {"samples": 0, "mean_ms": None, "p50_ms": None, "p90_ms": None, "p95_ms": None}
    return {
        "samples": len(clean),
        "mean_ms": mean(clean),
        "p50_ms": percentile(clean, 50),
        "p90_ms": percentile(clean, 90),
        "p95_ms": percentile(clean, 95),
    }


def summarize(events):
    groups = defaultdict(list)
    for event in events:
        key = (
            event["operation"],
            event.get("measurement_class") or "unclassified",
            event.get("provider_mode") or "unknown",
            event.get("run_temperature") or "unknown",
        )
        groups[key].append(event)

    output = []
    for (operation, measurement_class, provider_mode, temperature), items in sorted(groups.items()):
        successes = sum(event.get("success") is True for event in items)
        row = {
            "operation": operation,
            "measurement_class": measurement_class,
            "provider_mode": provider_mode,
            "run_temperature": temperature,
            "requests": len(items),
            "successes": successes,
            "failures": len(items) - successes,
            "success_rate": successes / len(items),
            "failure_rate": (len(items) - successes) / len(items),
            "total_latency": latency_stats(event.get("total_duration_ms") for event in items),
            "stages": {},
        }
        stage_names = sorted({name for event in items for name in event.get("durations_ms", {})})
        for name in stage_names:
            row["stages"][name] = latency_stats(
                event.get("durations_ms", {}).get(name) for event in items
            )
        if operation == "ingestion":
            valid_pages, valid_sizes = [], []
            for event in items:
                duration = event.get("total_duration_ms")
                if duration is None or duration <= 0:
                    continue
                seconds = duration / 1000
                pages = event.get("counts", {}).get("retained_pages")
                size = event.get("counts", {}).get("uploaded_bytes")
                if pages is not None:
                    valid_pages.append((pages, seconds))
                if size is not None:
                    valid_sizes.append((size, seconds))
            row["throughput"] = {
                "pages_per_second_mean": mean(p / s for p, s in valid_pages) if valid_pages else None,
                "mib_per_second_mean": mean((b / 1048576) / s for b, s in valid_sizes) if valid_sizes else None,
            }
        output.append(row)
    return output


def export_csv(events, path):
    stage_names = sorted({name for event in events for name in event.get("durations_ms", {})})
    count_names = sorted({name for event in events for name in event.get("counts", {})})
    fields = [
        "request_id", "timestamp", "operation", "success", "failure_category",
        "failure_stage", "measurement_class", "provider_mode", "run_temperature", "code_revision",
        "total_duration_ms", "cleanup_outcome",
    ] + [f"duration_{name}_ms" for name in stage_names] + [f"count_{name}" for name in count_names]
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for event in events:
            row = {field: event.get(field) for field in fields}
            for name in stage_names:
                row[f"duration_{name}_ms"] = event.get("durations_ms", {}).get(name)
            for name in count_names:
                row[f"count_{name}"] = event.get("counts", {}).get(name)
            writer.writerow(row)


def markdown_report(summary, malformed_count=0):
    lines = ["# Performance summary", "", f"Malformed JSONL records: {malformed_count}", ""]
    for group in summary:
        lines.extend([
            f"## {group['operation']} / {group['measurement_class']} / {group['provider_mode']} / {group['run_temperature']}", "",
            f"Samples: {group['requests']}; success rate: {group['success_rate']:.2%}; "
            f"failure rate: {group['failure_rate']:.2%}.", "",
            "Latency uses milliseconds and nearest-rank percentiles. Null values are excluded.", "",
            "| Metric | Samples | Mean ms | p50 ms | p90 ms | p95 ms |", "|---|---:|---:|---:|---:|---:|",
        ])
        metrics = {"total": group["total_latency"], **group["stages"]}
        for name, stats in metrics.items():
            values = ["—" if stats[key] is None else f"{stats[key]:.3f}" for key in ("mean_ms", "p50_ms", "p90_ms", "p95_ms")]
            lines.append(f"| {name} | {stats['samples']} | {' | '.join(values)} |")
        if "throughput" in group:
            throughput = group["throughput"]
            lines.extend(["", f"Mean pages/s: {throughput['pages_per_second_mean']}; mean MiB/s: {throughput['mib_per_second_mean']}."])
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--csv")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    events, malformed = load_events(args.input)
    summary = summarize(events)
    if args.csv:
        export_csv(events, args.csv)
    report = markdown_report(summary, len(malformed))
    if args.markdown:
        Path(args.markdown).write_text(report, encoding="utf-8")
    else:
        print(report)
    if malformed:
        print(json.dumps({"malformed": malformed}, indent=2))


if __name__ == "__main__":
    main()
