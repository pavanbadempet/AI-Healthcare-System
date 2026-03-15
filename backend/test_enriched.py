import httpx, json
base = "http://127.0.0.1:8000"

tests = [
    ("diabetes", {"hypertension":1,"high_chol":1,"bmi":35,"smoking_history":1,"heart_disease":1,"physical_activity":0,"general_health":5,"gender":1,"age":70}),
    ("heart", {"age":60,"sex":1,"cp":2,"trestbps":160,"chol":300,"fbs":1,"restecg":1,"thalach":110,"exang":1,"oldpeak":3.5,"slope":2,"ca":2,"thal":3}),
    ("liver", {"age":50,"gender":1,"total_bilirubin":5.0,"direct_bilirubin":2.5,"alkaline_phosphotase":500,"alamine_aminotransferase":120,"aspartate_aminotransferase":100,"total_proteins":5.5,"albumin":2.5,"albumin_and_globulin_ratio":0.5}),
    ("kidney", {"age":60,"bp":100,"sg":1.005,"al":4,"su":3,"rbc":0,"pc":0,"pcc":1,"ba":1,"bgr":300,"bu":150,"sc":5.0,"sod":120,"pot":6.0,"hemo":8,"pcv":25,"wc":12000,"rc":3.0,"htn":1,"dm":1,"cad":1,"appet":0,"pe":1,"ane":1}),
    ("lungs", {"gender":1,"age":65,"smoking":1,"yellow_fingers":1,"anxiety":1,"peer_pressure":1,"chronic_disease":1,"fatigue":1,"allergy":1,"wheezing":1,"alcohol":1,"coughing":1,"shortness_of_breath":1,"swallowing_difficulty":1,"chest_pain":1}),
]

for model, data in tests:
    r = httpx.post(f"{base}/predict/{model}", json=data)
    resp = r.json()
    print(f"\n{'='*60}")
    print(f"  {model.upper()} PREDICTION")
    print(f"{'='*60}")
    print(json.dumps(resp, indent=2))
