import os
import pandas as pd

def verify_classification_metrics(filepath):
    print("\n=========================================================")
    print(" HYPERION TELEMETRY | METRIC VERIFICATION PROTOCOL")
    print("=========================================================")
    
    if not os.path.exists(filepath):
        print(f"[!] Error: Telemetry file not found at {filepath}")
        return

    df = pd.read_csv(filepath)
    pred_col = 'HYPERION_PREDICTION' if 'HYPERION_PREDICTION' in df.columns else 'PINN_PREDICTION'
    
    TP = len(df[(df['ACTUAL_DISRUPTION'] == 1) & (df[pred_col] == 1)])
    FP = len(df[(df['ACTUAL_DISRUPTION'] == 0) & (df[pred_col] == 1)])
    FN = len(df[(df['ACTUAL_DISRUPTION'] == 1) & (df[pred_col] == 0)])
    TN = len(df[(df['ACTUAL_DISRUPTION'] == 0) & (df[pred_col] == 0)])
    
    total_samples = len(df)
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f" Dataset Sourced      : {os.path.basename(filepath)}")
    print(f" Total Samples (N)    : {total_samples}")
    print("---------------------------------------------------------")
    print(f" True Positives (TP)  : {TP}")
    print(f" False Positives (FP) : {FP}")
    print(f" False Negatives (FN) : {FN}")
    print(f" True Negatives (TN)  : {TN}")
    print("---------------------------------------------------------")
    print(f" Precision Verified   : {precision * 100:.2f}%")
    print(f" Recall Verified      : {recall * 100:.2f}%")
    print(f" F1-Score Verified    : {f1_score * 100:.2f}%")
    print("=========================================================\n")

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(__file__), '..', 'data', 'holdout')
    for fname in ['pristine_holdout_matrix.csv', 'diiid_holdout_matrix.csv', 'east_holdout_matrix.csv', 'cmod_archive_holdout_matrix.csv']:
        verify_classification_metrics(os.path.join(base, fname))