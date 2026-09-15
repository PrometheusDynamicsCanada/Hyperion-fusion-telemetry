# Hyperion PINN: Empirical Validation & Fusion Telemetry

**Physics-Informed Neural Networks for Disruption Forecasting**

This repository contains empirical validation telemetry from Hyperion, a proprietary Physics-Informed Neural Network (PINN) developed to forecast magnetohydrodynamic instability in fusion plasmas. 

The engine performs continuous thermodynamic inference under embedded plasma-physics constraints, enabling the prediction of instability before macroscopic containment failure.

---

## Proprietary Engine • Public Evidence

Hyperion is proprietary intellectual property. The underlying PINN architecture, optimization pipeline, training methodology, inference engine, and deployment framework are not distributed.

This repository is an empirical validation package, not an implementation release. It provides the telemetry and analysis artifacts required to independently verify the reported results, but not the proprietary engine used to generate them.

The repository includes:
* Raw validation telemetry
* Holdout evaluation matrices
* Plasma state vectors
* Inference logs
* Metric verification scripts

This allows independent reviewers to verify the reported empirical behavior without requiring access to proprietary implementation details. We are not asking reviewers to trust our implementation; we are asking reviewers to verify that the empirical results are accurately reported.

---

## The Central Claim
> **Despite evaluating completely unseen fusion shots, the PINN identifies thermodynamic instability hundreds of milliseconds before historical containment failure while achieving 93.10% precision on the provided holdout evaluation.**

Modern disruption prediction systems generally report abstract classification metrics (e.g., ROC-AUC or F1 scores). Our observations suggest that these metrics alone do not fully characterize operational usefulness. The critical operational quantity is **warning time**: *How much actionable time exists between the first physically meaningful instability and the actual disruption?*

Across the supplied validation telemetry, Hyperion identified thermodynamic divergence hundreds of milliseconds before historical containment loss.

---

## Key Empirical Evidence

### 1. Pristine Holdout Validation (MIT C-Mod)
Evaluation was performed against a strictly isolated, previously unseen holdout dataset to eliminate statistical overfitting. The model maintained high precision while providing an average warning interval substantially larger than the 10.0 ms evaluation baseline.

| Metric | Value |
| :--- | :--- |
| **Evaluation Samples (N)** | 47 |
| **Precision** | 93.10% |
| **Recall** | 65.85% |
| **F1 Score** | 77.14% |
| **False Positives** | 2 |
| **Average Warning Time** | **265.95 ms** |

**Result:** Hyperion exceeded the evaluation baseline by approximately 26×, providing an average warning interval of 265.95 ms while maintaining 93.10% precision on the holdout dataset.

### 2. Live Thermodynamic Audit
**Reference Shot:** MAST Tokamak Shot 29161 (S3 Uplink)

Rather than evaluating only the final disruption label, Hyperion continuously monitored the evolving thermodynamic state. 

```text
[000.00 ms] Baseline Plasma Nominal
   ↓
[305.50 ms] Kinetic deviation detected
   ↓
[310.20 ms] Topology degradation detected
   ↓
[318.80 ms] Volumetric saturation breach
   ↓
[318.80 ms] Predictive mitigation triggered
   ↓
[582.45 ms] Historical containment failure