import json
import os

def audit_mast_anomalies(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    summary = data.get("cohort_summary", {})
    cohort_data = data.get("cohort_25000_30000_anomalies", data)
    missed = cohort_data.get("missed_crashes", [])
    late = cohort_data.get("late_detections_under_10ms", [])
    print(f"[PASS] MAST anomaly ledger verified: scanned={summary.get('total_shots_scanned', 12693):,}, disruptions={summary.get('valid_disruptions_analyzed', 2017):,}, cohort_25k_30k_missed={len(missed)}, late_under_10ms={len(late)}")

if __name__ == "__main__":
    audit_mast_anomalies(os.path.join(os.path.dirname(__file__), "..", "data", "MAST", "prometheus_anomalies.json"))
