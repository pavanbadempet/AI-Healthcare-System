import pickle
import sys
import os
import warnings

# Suppress warnings during the upgrade process itself so we don't get flooded
warnings.filterwarnings("ignore")

models = [
    "Diabetes Model.pkl",
    "Heart Disease Model.pkl",
    "Liver Disease Model.pkl",
    "Scaler.pkl"
]

def upgrade_models():
    print("Starting Model Upgrade Process...")
    for model_name in models:
        try:
            if not os.path.exists(model_name):
                print(f"Skipping {model_name} (Not found)")
                continue

            print(f"Processing {model_name}...")
            
            # 1. Load with current library versions
            with open(model_name, 'rb') as f:
                obj = pickle.load(f)
            
            # 2. Re-save with current library versions
            with open(model_name, 'wb') as f:
                pickle.dump(obj, f)
                
            print(f"Successfully upgraded {model_name}")
            
        except Exception as e:
            print(f"FAILED to upgrade {model_name}: {e}")

if __name__ == "__main__":
    upgrade_models()
