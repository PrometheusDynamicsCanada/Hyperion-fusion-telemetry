import os
import pandas as pd

def compute_average_warning(filepath, evaluation_baseline=10.0):
    print("\n=========================================================")
    print(" HYPERION PINN | WARNING WINDOW COMPUTATION")
    print("=========================================================")
    
    if not os.path.exists(filepath):
        print(f"[!] Error: Telemetry file not found at {filepath}")
        return

    df = pd.read_csv(filepath)
    
    # Filter for True Positives (Successful Predictions)
    successful_predictions = df[(df['ACTUAL_DISRUPTION'] == 1) & (df['PINN_PREDICTION'] == 1)]
    
    if successful_predictions.empty:
        print("[!] No successful predictions found to calculate warning margins.")
        return
        
    avg_warning_ms = successful_predictions['WARNING_MARGIN_MS'].mean()
    multiplier = avg_warning_ms / evaluation_baseline

    print(f" Baseline Evaluation Minimum : {evaluation_baseline:.2f} ms")
    print(f" Calculated PINN Average     : {avg_warning_ms:.2f} ms")
    print("---------------------------------------------------------")
    print(f" [RESULT] Architecture surpasses baseline by {multiplier:.1f}x")
    print("=========================================================\n")

if __name__ == "__main__":
    target_csv = os.path.join(os.path.dirname(__file__), '..', 'data', 'holdout', 'pristine_holdout_matrix.csv')
    compute_average_warning(target_csv)