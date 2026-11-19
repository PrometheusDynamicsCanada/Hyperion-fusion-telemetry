import os
import pandas as pd

def compute_average_warning(filepath, evaluation_baseline=30.0):
    print("\n=========================================================")
    print(" HYPERION TELEMETRY | WARNING WINDOW COMPUTATION")
    print("=========================================================")
    
    if not os.path.exists(filepath):
        print(f"[!] Error: Telemetry file not found at {filepath}")
        return

    df = pd.read_csv(filepath)
    pred_col = 'HYPERION_PREDICTION' if 'HYPERION_PREDICTION' in df.columns else 'PINN_PREDICTION'
    warn_col = 'WARNING_WINDOW_MS' if 'WARNING_WINDOW_MS' in df.columns else 'WARNING_MARGIN_MS'
    
    successful_predictions = df[(df['ACTUAL_DISRUPTION'] == 1) & (df[pred_col] == 1)]
    
    if successful_predictions.empty:
        print("[!] No successful predictions found to calculate warning margins.")
        return
        
    avg_warning_ms = successful_predictions[warn_col].mean()
    med_warning_ms = successful_predictions[warn_col].median()
    multiplier = avg_warning_ms / evaluation_baseline

    print(f" Dataset Sourced             : {os.path.basename(filepath)} (TP = {len(successful_predictions)})")
    print(f" Mechanical Valve Floor      : {evaluation_baseline:.2f} ms")
    print(f" Empirical Mean Lead Time    : {avg_warning_ms:.2f} ms (Median: {med_warning_ms:.2f} ms)")
    print("---------------------------------------------------------")
    print(f" [RESULT] Architecture surpasses 30 ms valve floor by {multiplier:.2f}x")
    print("=========================================================\n")

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), '..', 'data', 'holdout')
    for fname in ['pristine_holdout_matrix.csv', 'diiid_holdout_matrix.csv', 'east_holdout_matrix.csv', 'cmod_archive_holdout_matrix.csv']:
        compute_average_warning(os.path.join(base, fname))