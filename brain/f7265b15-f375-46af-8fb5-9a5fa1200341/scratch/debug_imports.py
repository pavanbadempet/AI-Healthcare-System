import sys
import os

# Simulate what pytest might be doing
sys.path.append(os.getcwd())

import backend.prediction as pred1
from backend import ml_service
pred2 = ml_service.prediction

print(f"ID pred1 (backend.prediction): {id(pred1)}")
print(f"ID pred2 (ml_service.prediction): {id(pred2)}")
print(f"Are they the same? {pred1 is pred2}")

print("\n--- sys.modules containing 'prediction' ---")
for k in sys.modules:
    if 'prediction' in k:
        print(f"{k}: {sys.modules[k]}")
