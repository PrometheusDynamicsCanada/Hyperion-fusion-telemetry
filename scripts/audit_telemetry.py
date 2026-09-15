import os
import pandas as pd

def audit_plasma_state(filepath):
    print("\n=========================================================")
    print(" HYPERION PINN | THERMODYNAMIC CASCADE AUDIT")
    print("=========================================================")
    
    if not os.path.exists(filepath):
        print(f"[!] Error: Telemetry file not found at {filepath}")
        return

    df = pd.read_csv(filepath)
    
    print(" Analyzing timeline for thermodynamic degradation...")
    print("---------------------------------------------------------")
    
    for index, row in df.iterrows():
        timestamp = row['TIMESTAMP_MS']
        status = row['PINN_STATUS']
        
        if status != 'NOMINAL':
            if status == 'MITIGATION_PROTOCOL_TRIGGERED':
                print(f" [{timestamp:06.2f} ms] >>> {status.replace('_', ' ')} <<<")
                # Highlight the specific threshold values at the moment of trigger
                print(f"            * FLUID_IDX: {row['FLUID_INDEX_PDI']:.3f} | KINETIC_IDX: {row['KINETIC_INDEX_VDE']:.3f}")
            else:
                print(f" [{timestamp:06.2f} ms] {status.replace('_', ' ')}")
                
    print("=========================================================\n")

if __name__ == "__main__":
    target_csv = os.path.join(os.path.dirname(__file__), '..', 'data', 'telemetry', 'shot_29161_quad_vector_snapshot.csv')
    audit_plasma_state(target_csv)