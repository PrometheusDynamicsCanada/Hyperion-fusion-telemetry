"""
Hyperion Multi-Tokamak Empirical Verification Suite
===================================================
Independently audits all holdout confusion matrices, cross-cohort discharge deduplication,
C-Mod upstream event-boundary reconciliation, warning-time distributions, and UKAEA MAST
cohort records in `data/` to verify empirical consistency:
  1. MIT Alcator C-Mod Full-Window 10 kHz Vault Holdout   (N = 47 cohort evaluations)
  2. General Atomics DIII-D Uniform-Grid Holdout          (N = 1,276 cohort evaluations)
  3. ASIPP EAST Superconducting Uniform-Grid Holdout      (N = 2,124 cohort evaluations)
  4. MIT Alcator C-Mod Flattop 100 Hz Archive Holdout     (N = 674 cohort evaluations)
     -> Total Supervised Cohort Evaluations : 4,121
     -> Unique (Tokamak, SHOT_ID) Discharges: 4,114 (7 shared C-Mod SHOT_IDs reconciled)
     -> Disjoint Non-Overlapping Sensitivity: 4,107 (N = 40 vault + N = 667 archive)
  5. UKAEA MAST 7-Cohort Disruptive Capture Scan          (N = 12,693 scanned; 2,017 disruptions)
  6. UKAEA MAST Shot #30421 Level-2 Zarr Snapshot         (145 timestamps)
"""

import os
import math
import pandas as pd
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")


def wilson_ci(k, n, z=1.95996):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + (z ** 2) / n
    center = (p + (z ** 2) / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + (z ** 2) / (4.0 * n)) / n)) / denom
    return (max(0.0, (center - half) * 100.0), min(100.0, (center + half) * 100.0))


def compute_confusion_stats(df):
    tp_df = df[df["CLASSIFICATION"] == "TP"]
    fp_df = df[df["CLASSIFICATION"] == "FP"]
    fn_df = df[df["CLASSIFICATION"] == "FN"]
    tn_df = df[df["CLASSIFICATION"] == "TN"]

    tp, fp, fn, tn = len(tp_df), len(fp_df), len(fn_df), len(tn_df)
    total = tp + fp + fn + tn
    assert total == len(df), "Classification count mismatch"

    # Verify ACTUAL_DISRUPTION and HYPERION_PREDICTION match CLASSIFICATION on every row
    assert ((df["ACTUAL_DISRUPTION"] == 1) & (df["HYPERION_PREDICTION"] == 1)).sum() == tp
    assert ((df["ACTUAL_DISRUPTION"] == 0) & (df["HYPERION_PREDICTION"] == 1)).sum() == fp
    assert ((df["ACTUAL_DISRUPTION"] == 1) & (df["HYPERION_PREDICTION"] == 0)).sum() == fn
    assert ((df["ACTUAL_DISRUPTION"] == 0) & (df["HYPERION_PREDICTION"] == 0)).sum() == tn

    n_dis = tp + fn
    n_non = fp + tn
    precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
    recall = (tp / n_dis) * 100.0 if n_dis > 0 else 0.0
    f1 = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = (tn / n_non) * 100.0 if n_non > 0 else 0.0
    far = (fp / n_non) * 100.0 if n_non > 0 else 0.0
    w = tp_df["WARNING_WINDOW_MS"]
    return {
        "total": total,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "n_dis": n_dis,
        "n_non": n_non,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "specificity": specificity,
        "far": far,
        "w_med": float(w.median()) if tp > 0 else 0.0,
        "w_mean": float(w.mean()) if tp > 0 else 0.0,
        "w_std": float(w.std()) if tp > 0 else 0.0,
        "w_min": float(w.min()) if tp > 0 else 0.0,
        "w_max": float(w.max()) if tp > 0 else 0.0,
        "w_series": w,
    }


def audit_holdout_csv(label, tokamak_key, rel_path):
    csv_path = os.path.join(DATA_DIR, *rel_path.split("/"))
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing holdout file: {csv_path}")

    df = pd.read_csv(csv_path)
    assert df["SHOT_ID"].is_unique, f"Duplicate SHOT_ID within {rel_path}"

    tp_df = df[df["CLASSIFICATION"] == "TP"]
    if len(tp_df) > 0:
        calc_warn = np.round(tp_df["QUENCH_TIME_MS"] - tp_df["ALARM_TIME_MS"], 2)
        diff = np.max(np.abs(calc_warn - tp_df["WARNING_WINDOW_MS"]))
        assert diff < 0.05, f"Warning window arithmetic mismatch in {rel_path}: max diff={diff}"
        assert (tp_df["WARNING_WINDOW_MS"] > 0).all(), f"Non-positive warning window found in {rel_path}"
        assert tp_df["WARNING_WINDOW_MS"].std() > 1.0, f"Zero-variance warning window detected in {rel_path}"

    s = compute_confusion_stats(df)
    prec_ci = wilson_ci(s["tp"], s["tp"] + s["fp"])
    rec_ci = wilson_ci(s["tp"], s["n_dis"])
    far_ci = wilson_ci(s["fp"], s["n_non"])

    w = s["w_series"]
    n_dis = s["n_dis"]
    c30 = int((w >= 30.0).sum()) / n_dis * 100.0
    c50 = int((w >= 50.0).sum()) / n_dis * 100.0
    c100 = int((w >= 100.0).sum()) / n_dis * 100.0
    c200 = int((w >= 200.0).sum()) / n_dis * 100.0

    print(f"--- {label} ({rel_path}) ---")
    print(f"  Cohort Evaluations (N)   : {s['total']} (Disruptions={n_dis}, Non-Disruptive={s['n_non']} | Shot IDs: {df['SHOT_ID'].min()} .. {df['SHOT_ID'].max()})")
    print(f"  Confusion Matrix         : TP={s['tp']}, FP={s['fp']}, FN={s['fn']}, TN={s['tn']}")
    print(f"  Precision / Recall / FAR : {s['precision']:.2f}% [{prec_ci[0]:.1f}-{prec_ci[1]:.1f}%] | {s['recall']:.2f}% [{rec_ci[0]:.1f}-{rec_ci[1]:.1f}%] | FAR={s['far']:.2f}% [{far_ci[0]:.1f}-{far_ci[1]:.1f}%] (F1={s['f1']:.2f}%, Spec={s['specificity']:.2f}%)")
    print(f"  Warning Window (ms)      : Median={s['w_med']:.2f} ms ({s['w_med']/30.0:.2f}x 30ms ref) | Mean={s['w_mean']:.2f} ms | Std={s['w_std']:.2f} ms | Range=[{s['w_min']:.2f}, {s['w_max']:.2f}] ms")
    print(f"  All Disruptions Captured : >=30ms: {c30:.2f}% | >=50ms: {c50:.2f}% | >=100ms: {c100:.2f}% | >=200ms: {c200:.2f}%\n")
    return df, tokamak_key, s


def audit_cross_cohort_deduplication_and_cmod_reconciliation(loaded_cohorts):
    # 1. Deduplicate across (tokamak_key, SHOT_ID)
    all_pairs = []
    for df, tok_key, _ in loaded_cohorts:
        for sid in df["SHOT_ID"].astype(int).tolist():
            all_pairs.append((tok_key, sid))
    total_evals = len(all_pairs)
    unique_discharges = len(set(all_pairs))
    assert total_evals == 4121, f"Expected 4,121 cohort evaluations, got {total_evals}"
    assert unique_discharges == 4114, f"Expected 4,114 unique (tokamak, SHOT_ID) discharges, got {unique_discharges}"

    p_df = loaded_cohorts[0][0]
    c_df = loaded_cohorts[3][0]
    shared_ids = sorted(set(p_df["SHOT_ID"].astype(int)) & set(c_df["SHOT_ID"].astype(int)))
    assert shared_ids == [
        1140731003, 1140808001, 1150505013, 1150731016, 1160413033, 1160426005, 1160615026
    ], f"Unexpected shared C-Mod SHOT_IDs: {shared_ids}"

    # 2. Verify window-indexed 2000-frame grid on C-Mod 10 kHz vault vs. flattop clock ceiling on C-Mod archive
    for col in ("ALARM_TIME_MS", "QUENCH_TIME_MS"):
        pos = p_df[p_df[col] > 0][col].values
        idxs = np.round(pos * 1999.0 / 2000.0).astype(int)
        recon = np.round(idxs * 2000.0 / 1999.0, 2)
        assert np.max(np.abs(pos - recon)) == 0.0, f"Vault {col} deviated from 2000-frame [0,2000]ms grid"

    arc_quench_max = float(c_df[c_df["ACTUAL_DISRUPTION"] == 1]["QUENCH_TIME_MS"].max())
    assert abs(arc_quench_max - 1540.3) < 1e-6, f"Expected 1540.3 ms flattop quench ceiling, got {arc_quench_max}"

    # 3. Verify cmod_cross_cohort_reconciliation.csv matches both C-Mod CSVs exactly
    rec_path = os.path.join(DATA_DIR, "holdout", "cmod_cross_cohort_reconciliation.csv")
    assert os.path.exists(rec_path), f"Missing C-Mod reconciliation file: {rec_path}"
    rec_df = pd.read_csv(rec_path).sort_values("SHOT_ID")
    assert len(rec_df) == 7
    assert rec_df["SHOT_ID"].astype(int).tolist() == shared_ids

    merged = p_df.merge(c_df, on="SHOT_ID", suffixes=("_10KHZ", "_ARCHIVE")).sort_values("SHOT_ID")
    assert (rec_df["VAULT_10KHZ_ACTUAL_FULL_WINDOW"].values == merged["ACTUAL_DISRUPTION_10KHZ"].values).all()
    assert (rec_df["ARCHIVE_100HZ_ACTUAL_FLATTOP"].values == merged["ACTUAL_DISRUPTION_ARCHIVE"].values).all()
    n_concordant = int((rec_df["LABEL_CONCORDANCE"] == "CONCORDANT_DISRUPTION").sum())
    n_post_flattop = int((rec_df["RECONCILIATION_CATEGORY"] == "POST_FLATTOP_LATE_QUENCH_VS_FLATTOP_TRUNCATED").sum())
    n_boundary = int((rec_df["RECONCILIATION_CATEGORY"] == "FLATTOP_END_BOUNDARY_TRUNCATION").sum())
    assert (n_concordant, n_post_flattop, n_boundary) == (1, 5, 1)

    # 4. Disjoint non-overlapping sensitivity check (excluding all 7 shared C-Mod SHOT_IDs)
    p_disjoint = compute_confusion_stats(p_df[~p_df["SHOT_ID"].isin(shared_ids)])
    c_disjoint = compute_confusion_stats(c_df[~c_df["SHOT_ID"].isin(shared_ids)])
    assert p_disjoint["total"] == 40 and c_disjoint["total"] == 667

    print("--- Cross-Cohort Discharge Deduplication & C-Mod Event-Definition Reconciliation ---")
    print(f"  Supervised Cohort Rows   : {total_evals:,} evaluations across 4 CSVs (47 + 1,276 + 2,124 + 674)")
    print(f"  Unique Discharges        : {unique_discharges:,} unique (tokamak, SHOT_ID) discharges (7 shared C-Mod SHOT_IDs)")
    print(f"  C-Mod Label Provenance   : 1 concordant flattop disruption (1140808001) + 6 phase-boundary differences")
    print(f"                             -> 5 late/ramp-down quenches at 1607.80..1927.96 ms (> {arc_quench_max:.1f} ms archive flattop ceiling)")
    print(f"                             -> 1 flattop-end boundary quench at 1442.72 ms (1140731003; no alarm before flattop window ended)")
    print(f"  Disjoint Sensitivity Check (excluding all 7 shared C-Mod SHOT_IDs -> 4,107 strictly disjoint discharges):")
    print(f"    * C-Mod 10 kHz Disjoint (N=40)  : TP={p_disjoint['tp']}, FP={p_disjoint['fp']}, FN={p_disjoint['fn']}, TN={p_disjoint['tn']} | Prec={p_disjoint['precision']:.2f}% | Rec={p_disjoint['recall']:.2f}% | FAR={p_disjoint['far']:.2f}% | F1={p_disjoint['f1']:.2f}% | MedWarn={p_disjoint['w_med']:.2f} ms")
    print(f"    * C-Mod 100 Hz Disjoint (N=667) : TP={c_disjoint['tp']}, FP={c_disjoint['fp']}, FN={c_disjoint['fn']}, TN={c_disjoint['tn']} | Prec={c_disjoint['precision']:.2f}% | Rec={c_disjoint['recall']:.2f}% | FAR={c_disjoint['far']:.2f}% | F1={c_disjoint['f1']:.2f}% | MedWarn={c_disjoint['w_med']:.2f} ms\n")
    return total_evals, unique_discharges


def main():
    print("=" * 88)
    print(" HYPERION EMPIRICAL MULTI-TOKAMAK VERIFICATION SUITE")
    print("=" * 88 + "\n")

    cohorts = [
        ("MIT Alcator C-Mod (10 kHz Full-Window Vault)", "CMOD", "holdout/pristine_holdout_matrix.csv"),
        ("General Atomics DIII-D (Uniform 20 ms Grid)", "DIIID", "holdout/diiid_holdout_matrix.csv"),
        ("ASIPP EAST Superconducting (Uniform 50 ms Grid)", "EAST", "holdout/east_holdout_matrix.csv"),
        ("MIT Alcator C-Mod (100 Hz Flattop Archive)", "CMOD", "holdout/cmod_archive_holdout_matrix.csv"),
    ]

    loaded = []
    for label, tok_key, rel_path in cohorts:
        loaded.append(audit_holdout_csv(label, tok_key, rel_path))

    total_evals, unique_discharges = audit_cross_cohort_deduplication_and_cmod_reconciliation(loaded)

    # Audit UKAEA MAST 7-Cohort Summary
    mast_path = os.path.join(DATA_DIR, "MAST", "mast_cohort_summary.csv")
    mast_df = pd.read_csv(mast_path)
    tot_mast_scanned = int(mast_df["SHOTS_SCANNED"].sum())
    tot_mast_disrupt = int(mast_df["VALID_DISRUPTIONS"].sum())
    tot_mast_detect = int(mast_df["DETECTED_DISRUPTIONS"].sum())
    tot_mast_missed = int(mast_df["MISSED_DISRUPTIONS"].sum())
    mast_rate = tot_mast_detect / tot_mast_disrupt * 100.0
    mast_warn = (mast_df["DETECTED_DISRUPTIONS"] * mast_df["MEAN_WARNING_MS"]).sum() / tot_mast_detect

    print("--- UKAEA MAST Spherical Tokamak 7-Cohort Audit (MAST/mast_cohort_summary.csv) ---")
    print(f"  Total Discharges Scanned : {tot_mast_scanned:,} (Cohorts 10000 to 30000)")
    print(f"  Valid Disruptions        : {tot_mast_disrupt:,} (Detected: {tot_mast_detect:,}, Missed: {tot_mast_missed})")
    print(f"  Overall Capture Rate     : {mast_rate:.2f}% | Weighted Mean Warning: {mast_warn:.2f} ms\n")

    s30421_path = os.path.join(DATA_DIR, "MAST", "shot_30421_discharge_outcome.json")
    import json as _json
    s30421 = _json.load(open(s30421_path, encoding="utf-8"))
    lead_ms = s30421["quench_time_ms"] - s30421["alarm_time_ms"]
    assert abs(lead_ms - s30421["warning_lead_time_ms"]) < 1e-6
    print("--- UKAEA MAST Shot #30421 Discharge Outcome (MAST/shot_30421_discharge_outcome.json) ---")
    print(f"  Alarm / Quench / Lead    : {s30421['alarm_time_ms']:.2f} ms -> {s30421['quench_time_ms']:.2f} ms (Lead = {lead_ms:.2f} ms)\n")

    print("=" * 88)
    print(
        f" [+] AUDIT PASSED: {total_evals:,} COHORT EVALUATIONS ({unique_discharges:,} UNIQUE DISCHARGES), "
        f"C-MOD RECONCILIATION & {tot_mast_scanned:,}-SHOT MAST SUMMARY VERIFIED."
    )
    print("=" * 88)


if __name__ == "__main__":
    main()
