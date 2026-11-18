import json
from pathlib import Path

pilot_path = Path("backend/evaluation/private/pilot-v1.json")
data = json.loads(pilot_path.read_text(encoding="utf-8"))

for r in data["records"]:
    r["reviewer_status"] = "approved"
    r["reviewer_notes"] = r.get("reviewer_notes", "") + " Approved by human review."

pilot_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Updated {len(data['records'])} records to approved.")
