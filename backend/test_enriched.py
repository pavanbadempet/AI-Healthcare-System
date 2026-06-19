"""
Comprehensive Bug Hunt — Tests ALL endpoints, edge cases, and error handling
"""
import os

import httpx

BASE = "http://127.0.0.1:8000"
bugs = []
passes = []

def check(name, condition, detail=""):
    if condition:
        passes.append(name)
    else:
        bugs.append(f"BUG: {name} — {detail}")

# ============================================================
# 1. Health check
# ============================================================
r = httpx.get(f"{BASE}/healthz")
check("Health endpoint", r.status_code == 200, f"Got {r.status_code}")

# ============================================================
# 2. All 5 predictions return enriched responses
# ============================================================
diabetes_data = {"hypertension":1,"high_chol":1,"bmi":32,"smoking_history":1,"heart_disease":0,"physical_activity":0,"general_health":4,"gender":1,"age":55}
r = httpx.post(f"{BASE}/predict/diabetes", json=diabetes_data)
d = r.json()
check("Diabetes returns 200", r.status_code == 200, f"Got {r.status_code}")
check("Diabetes has prediction", "prediction" in d, f"Keys: {d.keys()}")
check("Diabetes has confidence", "confidence" in d and d["confidence"] is not None, f"confidence={d.get('confidence')}")
check("Diabetes has risk_level", "risk_level" in d and d["risk_level"] is not None, f"risk_level={d.get('risk_level')}")
check("Diabetes has disclaimer", "disclaimer" in d and len(d.get("disclaimer",""))>0, "disclaimer missing")

heart_data = {"age":55,"sex":1,"cp":1,"trestbps":28,"chol":1,"fbs":1,"restecg":3,"thalach":1,"exang":0,"oldpeak":0,"slope":0,"ca":0,"thal":0}
r = httpx.post(f"{BASE}/predict/heart", json=heart_data)
d = r.json()
check("Heart returns 200", r.status_code == 200, f"Got {r.status_code}")
check("Heart has confidence", "confidence" in d and d["confidence"] is not None, f"confidence={d.get('confidence')}")
check("Heart has risk_level", "risk_level" in d, "Missing risk_level")

liver_data = {"age":45,"gender":1,"total_bilirubin":1.2,"direct_bilirubin":0.3,"alkaline_phosphotase":200,"alamine_aminotransferase":40,"aspartate_aminotransferase":35,"total_proteins":6.8,"albumin":3.5,"albumin_and_globulin_ratio":0.9}
r = httpx.post(f"{BASE}/predict/liver", json=liver_data)
d = r.json()
check("Liver returns 200", r.status_code == 200, f"Got {r.status_code}")
check("Liver has confidence", "confidence" in d and d["confidence"] is not None, f"confidence={d.get('confidence')}")

kidney_data = {"age":55,"bp":80,"sg":1.02,"al":1,"su":0,"rbc":1,"pc":1,"pcc":0,"ba":0,"bgr":121,"bu":36,"sc":1.2,"sod":135,"pot":3.5,"hemo":15.4,"pcv":44,"wc":7800,"rc":5.2,"htn":1,"dm":1,"cad":0,"appet":0,"pe":0,"ane":0}
r = httpx.post(f"{BASE}/predict/kidney", json=kidney_data)
d = r.json()
check("Kidney returns 200", r.status_code == 200, f"Got {r.status_code}")
check("Kidney has confidence", "confidence" in d and d["confidence"] is not None, f"confidence={d.get('confidence')}")

lungs_data = {"gender":1,"age":65,"smoking":1,"yellow_fingers":1,"anxiety":0,"peer_pressure":0,"chronic_disease":1,"fatigue":1,"allergy":0,"wheezing":1,"alcohol":1,"coughing":1,"shortness_of_breath":1,"swallowing_difficulty":0,"chest_pain":1}
r = httpx.post(f"{BASE}/predict/lungs", json=lungs_data)
d = r.json()
check("Lungs returns 200", r.status_code == 200, f"Got {r.status_code}")
check("Lungs has confidence", "confidence" in d and d["confidence"] is not None, f"confidence={d.get('confidence')}")

# ============================================================
# 3. Edge cases — missing fields
# ============================================================
r = httpx.post(f"{BASE}/predict/diabetes", json={"hypertension":1})
check("Diabetes missing fields -> 422", r.status_code == 422, f"Got {r.status_code}")

r = httpx.post(f"{BASE}/predict/heart", json={})
check("Heart empty body -> 422", r.status_code == 422, f"Got {r.status_code}")

r = httpx.post(f"{BASE}/predict/liver", json={"age":30})
check("Liver missing fields -> 422", r.status_code == 422, f"Got {r.status_code}")

# ============================================================
# 4. Edge cases — extreme values
# ============================================================
extreme_diabetes = {"hypertension":0,"high_chol":0,"bmi":0,"smoking_history":0,"heart_disease":0,"physical_activity":0,"general_health":1,"gender":0,"age":0}
r = httpx.post(f"{BASE}/predict/diabetes", json=extreme_diabetes)
check("Diabetes BMI=0 doesn't crash", r.status_code == 200, f"Got {r.status_code}")

extreme_diabetes2 = {"hypertension":1,"high_chol":1,"bmi":100,"smoking_history":1,"heart_disease":1,"physical_activity":1,"general_health":5,"gender":1,"age":120}
r = httpx.post(f"{BASE}/predict/diabetes", json=extreme_diabetes2)
check("Diabetes extreme values don't crash", r.status_code == 200, f"Got {r.status_code}")

# ============================================================
# 5. Auth endpoints
# ============================================================
admin_username = os.getenv("DEFAULT_ADMIN_USERNAME")
admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
if admin_username and admin_password:
    r = httpx.post(f"{BASE}/token", data={"username": admin_username, "password": admin_password})
    check("Configured admin login works", r.status_code == 200, f"Got {r.status_code}")
else:
    r = None
    check("Configured admin login skipped when bootstrap credentials are unset", True)

if r is not None and r.status_code == 200:
    token = r.json()["access_token"]

    # Profile
    r2 = httpx.get(f"{BASE}/profile", headers={"Authorization":f"Bearer {token}"})
    check("Profile endpoint works", r2.status_code == 200, f"Got {r2.status_code}")

    # Records
    r3 = httpx.get(f"{BASE}/records", headers={"Authorization":f"Bearer {token}"})
    check("Records endpoint works", r3.status_code == 200, f"Got {r3.status_code}")

    # Admin stats
    r4 = httpx.get(f"{BASE}/admin/stats", headers={"Authorization":f"Bearer {token}"})
    check("Admin stats works", r4.status_code == 200, f"Got {r4.status_code}")

# ============================================================
# 6. Unauth access
# ============================================================
r = httpx.get(f"{BASE}/profile")
check("Profile without auth → 401", r.status_code == 401, f"Got {r.status_code}")

# ============================================================
# 7. Invalid endpoint
# ============================================================
r = httpx.get(f"{BASE}/predict/nonexistent")
check("Invalid prediction → 404/405", r.status_code in [404, 405], f"Got {r.status_code}")

# ============================================================
# 8. Frontend accessibility
# ============================================================
r = httpx.get("http://127.0.0.1:3000", follow_redirects=True)
check("Frontend loads", r.status_code == 200, f"Got {r.status_code}")

r = httpx.get("http://127.0.0.1:3000/login", follow_redirects=True)
check("Login page loads", r.status_code == 200, f"Got {r.status_code}")

# ============================================================
# REPORT
# ============================================================
print(f"\n{'='*60}")
print("  BUG HUNT RESULTS")
print(f"{'='*60}")
print(f"\nPASSED: {len(passes)}")
for p in passes:
    print(f"  [OK] {p}")

if bugs:
    print(f"\nBUGS FOUND: {len(bugs)}")
    for b in bugs:
        print(f"  [FAIL] {b}")
else:
    print("\n>> NO BUGS FOUND!")

print(f"\nTotal: {len(passes)} passed, {len(bugs)} bugs")
