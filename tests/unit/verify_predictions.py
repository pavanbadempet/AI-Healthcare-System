"""
Real-World Prediction Validation v2 — Actual records from training datasets.
Fixed: lung encoding (0/1 not 1/2), heart model retrained with class balancing.
"""
import httpx
import pandas as pd

BASE = "http://127.0.0.1:8000"
results = []

def test(model, case_name, expected, payload):
    try:
        r = httpx.post(f"{BASE}/predict/{model}", json=payload, timeout=10)
        if r.status_code == 200:
            actual = r.json()["prediction"]
            match = "PASS" if actual == expected else "DIFF"
            results.append((model.upper(), case_name, expected, actual, match))
        else:
            results.append((model.upper(), case_name, expected, f"HTTP {r.status_code}", "FAIL"))
    except Exception as e:
        results.append((model.upper(), case_name, expected, str(e)[:50], "FAIL"))

# ═══════════════════ DIABETES (BRFSS) ═══════════════════
df = pd.read_parquet("data/processed/diabetes.parquet")
for i, (_, row) in enumerate(df[df["diabetes"]==0].head(5).iterrows()):
    test("diabetes", f"BRFSS healthy #{i+1}", "Low Risk",
         {"hypertension":int(row["HighBP"]),"high_chol":int(row["HighChol"]),"bmi":float(row["BMI"]),"smoking_history":int(row["Smoker"]),"heart_disease":int(row["HeartDiseaseorAttack"]),"physical_activity":int(row["PhysActivity"]),"general_health":int(row["GenHlth"]),"gender":int(row["Sex"]),"age":float(row["Age"])})
for i, (_, row) in enumerate(df[df["diabetes"]==1].head(5).iterrows()):
    test("diabetes", f"BRFSS diabetic #{i+6}", "High Risk",
         {"hypertension":int(row["HighBP"]),"high_chol":int(row["HighChol"]),"bmi":float(row["BMI"]),"smoking_history":int(row["Smoker"]),"heart_disease":int(row["HeartDiseaseorAttack"]),"physical_activity":int(row["PhysActivity"]),"general_health":int(row["GenHlth"]),"gender":int(row["Sex"]),"age":float(row["Age"])})

# ═══════════════════ HEART (BRFSS mapped) ═══════════════════
hdf = pd.read_parquet("data/processed/heart.parquet")
for i, (_, row) in enumerate(hdf[hdf["target"]==0].head(5).iterrows()):
    test("heart", f"BRFSS heart healthy #{i+1}", "Healthy Heart",
         {"age":float(row["age"]),"sex":int(row["sex"]),"cp":int(row["high_bp"]),"trestbps":float(row["bmi"]),"chol":int(row["high_chol"]),"fbs":int(row["smoker"]),"restecg":int(row["gen_hlth"]),"thalach":int(row["phys_activity"]),"exang":int(row["stroke"]),"oldpeak":float(row["diabetes"]),"slope":int(row["hvy_alcohol"]),"ca":0,"thal":0})
for i, (_, row) in enumerate(hdf[hdf["target"]==1].head(5).iterrows()):
    test("heart", f"BRFSS heart disease #{i+6}", "Heart Disease Detected",
         {"age":float(row["age"]),"sex":int(row["sex"]),"cp":int(row["high_bp"]),"trestbps":float(row["bmi"]),"chol":int(row["high_chol"]),"fbs":int(row["smoker"]),"restecg":int(row["gen_hlth"]),"thalach":int(row["phys_activity"]),"exang":int(row["stroke"]),"oldpeak":float(row["diabetes"]),"slope":int(row["hvy_alcohol"]),"ca":0,"thal":0})

# ═══════════════════ LIVER (ILPD) ═══════════════════
ldf = pd.read_parquet("data/processed/liver.parquet")
for i, (_, row) in enumerate(ldf[ldf["target"]==0].head(5).iterrows()):
    test("liver", f"ILPD healthy #{i+1}", "Healthy Liver",
         {"age":float(row["age"]),"gender":int(row["gender"]),"total_bilirubin":float(row["total_bilirubin"]),"direct_bilirubin":float(row["direct_bilirubin"]),"alkaline_phosphotase":float(row["alkaline_phosphotase"]),"alamine_aminotransferase":float(row["alamine_aminotransferase"]),"aspartate_aminotransferase":float(row["aspartate_aminotransferase"]),"total_proteins":float(row["total_proteins"]),"albumin":float(row["albumin"]),"albumin_and_globulin_ratio":float(row["albumin_and_globulin_ratio"])})
for i, (_, row) in enumerate(ldf[ldf["target"]==1].head(5).iterrows()):
    test("liver", f"ILPD disease #{i+6}", "Liver Disease Detected",
         {"age":float(row["age"]),"gender":int(row["gender"]),"total_bilirubin":float(row["total_bilirubin"]),"direct_bilirubin":float(row["direct_bilirubin"]),"alkaline_phosphotase":float(row["alkaline_phosphotase"]),"alamine_aminotransferase":float(row["alamine_aminotransferase"]),"aspartate_aminotransferase":float(row["aspartate_aminotransferase"]),"total_proteins":float(row["total_proteins"]),"albumin":float(row["albumin"]),"albumin_and_globulin_ratio":float(row["albumin_and_globulin_ratio"])})

# ═══════════════════ KIDNEY (UCI CKD) ═══════════════════
kdf = pd.read_parquet("data/processed/kidney.parquet")
for i, (_, row) in enumerate(kdf[kdf["target"]==0].head(4).iterrows()):
    test("kidney", f"UCI kidney healthy #{i+1}", "Healthy Kidney",
         {"age":float(row["age"]),"bp":float(row["bp"]),"sg":float(row["sg"]),"al":float(row["al"]),"su":float(row["su"]),"rbc":int(row["rbc"]),"pc":int(row["pc"]),"pcc":int(row["pcc"]),"ba":int(row["ba"]),"bgr":float(row["bgr"]),"bu":float(row["bu"]),"sc":float(row["sc"]),"sod":float(row["sod"]),"pot":float(row["pot"]),"hemo":float(row["hemo"]),"pcv":float(row["pcv"]),"wc":float(row["wc"]),"rc":float(row["rc"]),"htn":int(row["htn"]),"dm":int(row["dm"]),"cad":int(row["cad"]),"appet":int(row["appet"]),"pe":int(row["pe"]),"ane":int(row["ane"])})
for i, (_, row) in enumerate(kdf[kdf["target"]==1].head(4).iterrows()):
    test("kidney", f"UCI kidney CKD #{i+5}", "Chronic Kidney Disease Detected",
         {"age":float(row["age"]),"bp":float(row["bp"]),"sg":float(row["sg"]),"al":float(row["al"]),"su":float(row["su"]),"rbc":int(row["rbc"]),"pc":int(row["pc"]),"pcc":int(row["pcc"]),"ba":int(row["ba"]),"bgr":float(row["bgr"]),"bu":float(row["bu"]),"sc":float(row["sc"]),"sod":float(row["sod"]),"pot":float(row["pot"]),"hemo":float(row["hemo"]),"pcv":float(row["pcv"]),"wc":float(row["wc"]),"rc":float(row["rc"]),"htn":int(row["htn"]),"dm":int(row["dm"]),"cad":int(row["cad"]),"appet":int(row["appet"]),"pe":int(row["pe"]),"ane":int(row["ane"])})

# ═══════════════════ LUNGS (Survey, 0/1 encoding) ═══════════════════
ludf = pd.read_parquet("data/processed/lungs.parquet")
for i, (_, row) in enumerate(ludf[ludf["target"]==0].head(5).iterrows()):
    test("lungs", f"Survey lungs healthy #{i+1}", "Healthy Lungs",
         {"gender":int(row["GENDER"]),"age":int(row["AGE"]),"smoking":int(row["SMOKING"]),"yellow_fingers":int(row["YELLOW_FINGERS"]),"anxiety":int(row["ANXIETY"]),"peer_pressure":int(row["PEER_PRESSURE"]),"chronic_disease":int(row["CHRONIC_DISEASE"]),"fatigue":int(row["FATIGUE"]),"allergy":int(row["ALLERGY"]),"wheezing":int(row["WHEEZING"]),"alcohol":int(row["ALCOHOL_CONSUMING"]),"coughing":int(row["COUGHING"]),"shortness_of_breath":int(row["SHORTNESS_OF_BREATH"]),"swallowing_difficulty":int(row["SWALLOWING_DIFFICULTY"]),"chest_pain":int(row["CHEST_PAIN"])})
for i, (_, row) in enumerate(ludf[ludf["target"]==1].head(5).iterrows()):
    test("lungs", f"Survey lungs cancer #{i+6}", "Respiratory Issue Detected",
         {"gender":int(row["GENDER"]),"age":int(row["AGE"]),"smoking":int(row["SMOKING"]),"yellow_fingers":int(row["YELLOW_FINGERS"]),"anxiety":int(row["ANXIETY"]),"peer_pressure":int(row["PEER_PRESSURE"]),"chronic_disease":int(row["CHRONIC_DISEASE"]),"fatigue":int(row["FATIGUE"]),"allergy":int(row["ALLERGY"]),"wheezing":int(row["WHEEZING"]),"alcohol":int(row["ALCOHOL_CONSUMING"]),"coughing":int(row["COUGHING"]),"shortness_of_breath":int(row["SHORTNESS_OF_BREATH"]),"swallowing_difficulty":int(row["SWALLOWING_DIFFICULTY"]),"chest_pain":int(row["CHEST_PAIN"])})

# ═══════════════════ RESULTS ═══════════════════
print()
print(f"{'Model':<12} {'Test Case':<42} {'Expected':<32} {'Actual':<32} {'OK'}")
print("=" * 122)
for model, case, exp, act, match in results:
    print(f"{model:<12} {case:<42} {exp:<32} {act:<32} {match}")

total = len(results)
passed = sum(1 for r in results if r[4] == "PASS")
diff = sum(1 for r in results if r[4] == "DIFF")
fail = sum(1 for r in results if r[4] == "FAIL")
print(f"\nTotal: {total} | PASS: {passed} ({100*passed//total}%) | DIFF: {diff} | FAIL: {fail}")

# Per-model breakdown
for m in ["DIABETES","HEART","LIVER","KIDNEY","LUNGS"]:
    mr = [r for r in results if r[0]==m]
    mp = sum(1 for r in mr if r[4]=="PASS")
    print(f"  {m}: {mp}/{len(mr)} correct")
