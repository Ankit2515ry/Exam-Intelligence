import json
from pathlib import Path
import statistics

res_path = Path("backend/evaluation/results/pilot-v1/evaluation-results.json")
data = json.loads(res_path.read_text(encoding="utf-8"))

print("=" * 80)
print("EXAM INTELLIGENCE - PHASE 4E PILOT RETRIEVAL EVALUATION RESULTS")
print("=" * 80)

print(f"\nRun ID: {data['run_id']}")
print(f"Timestamp: {data['timestamp']}")
print(f"Dataset Version: {data['dataset_version']}")
print(f"Corpus Version: {data['corpus_version']}")
print(f"Total Questions Evaluated: {data['sample_count']}")

rm = data["retrieval_metrics"]
print("\n--- AGGREGATE RETRIEVAL METRICS (13 Eligible Answerable Questions) ---")
print(f"  Hit Rate @ 5:    {rm['hit_at_5'] * 100:.2f}% ({rm['hit_at_5']:.4f})")
print(f"  Precision @ 5:   {rm['precision_at_5'] * 100:.2f}% ({rm['precision_at_5']:.4f})")
print(f"  Recall @ 5:      {rm['recall_at_5'] * 100:.2f}% ({rm['recall_at_5']:.4f})")
print(f"  MRR @ 10:        {rm['mrr_at_10']:.4f}")
print(f"  nDCG @ 5:        {rm['ndcg_at_5']:.4f}")
print(f"  Eligible / Evaluated: {rm['eligible_questions']} / {data['sample_count']}")
print(f"  Excluded (Unanswerable): {rm['excluded_no_relevance_labels']}")

lats = data["latency"]["retrieval_per_question_ms"]
print("\n--- RETRIEVAL EXECUTION LATENCY ---")
print(f"  Total In-Process Evaluation Time: {data['latency']['total_run_ms']:.2f} ms")
print(f"  Average Retrieval Time:           {statistics.mean(lats):.2f} ms")
print(f"  Median Retrieval Time:            {statistics.median(lats):.2f} ms")
print(f"  Min Retrieval Time:               {min(lats):.2f} ms")
print(f"  Max Retrieval Time (cold-start):  {max(lats):.2f} ms")
print(f"  Warm Average (queries 2-15):      {statistics.mean(lats[1:]):.2f} ms")

print("\n--- PER-QUESTION BREAKDOWN ---")
print(f"{'QID':4} | {'Category':24} | {'Elig':5} | {'Hit@5':6} | {'P@5':5} | {'R@5':5} | {'MRR':5} | {'nDCG@5':6} | {'Dur (ms)':8}")
print("-" * 88)

for q in data["per_question"]:
    qid = q["question_id"]
    ret = q.get("retrieval") or {}
    dur = q.get("retrieval_duration_ms", 0)
    
    # find category from pilot-v1.json
    pilot = json.loads(Path("backend/evaluation/private/pilot-v1.json").read_text(encoding="utf-8"))
    cat = [x["category"] for x in pilot["records"] if x["question_id"] == qid][0]
    
    if ret.get("eligible"):
        print(f"{qid:4} | {cat:24} | {'Yes':5} | {ret['hit_at_5']:6.1f} | {ret['precision_at_5']:5.2f} | {ret['recall_at_5']:5.2f} | {ret['mrr_at_10']:5.2f} | {ret['ndcg_at_5']:6.2f} | {dur:8.1f}")
    else:
        print(f"{qid:4} | {cat:24} | {'No':5} | {'N/A':6} | {'N/A':5} | {'N/A':5} | {'N/A':5} | {'N/A':6} | {dur:8.1f}")

print("-" * 88)
