import logging
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from backend.fhir import fhir_datetime

logger = logging.getLogger(__name__)

CARE_PLAN_TEMPLATES = {
    "diabetes": {
        "title": "Type 2 Diabetes Mellitus Management Plan",
        "description": "Comprehensive care plan for glycemic control and lifestyle modification.",
        "goals": ["Maintain HbA1c below 7.0%", "Achieve fasting blood glucose between 80-130 mg/dL"],
        "activities": [
            {"name": "Self-Monitoring of Blood Glucose", "detail": "Check fasting blood sugar daily and post-prandially twice weekly."},
            {"name": "Dietary Intervention", "detail": "Implement a structured low-glycemic, low-carbohydrate nutrition plan."},
            {"name": "Physical Activity Protocol", "detail": "Engage in at least 150 minutes of moderate-intensity aerobic exercise per week."}
        ]
    },
    "heart": {
        "title": "Cardiovascular Disease Management Plan",
        "description": "Care plan targeted at lowering blood pressure, lipid profile management, and cardiac care.",
        "goals": ["Maintain Blood Pressure below 130/80 mmHg", "LDL Cholesterol below 70 mg/dL"],
        "activities": [
            {"name": "Vitals Monitoring", "detail": "Check blood pressure and heart rate daily before morning medication."},
            {"name": "Cardioprotective Nutrition", "detail": "Adopt a low-sodium, Mediterranean-style diet (< 1500mg sodium daily)."},
            {"name": "Cardiology Consultation", "detail": "Schedule follow-up cardiology evaluation with stress testing as needed."}
        ]
    },
    "kidney": {
        "title": "Chronic Kidney Disease Progression Management Plan",
        "description": "Renal protection care plan focused on slowing GFR decline and avoiding nephrotoxicity.",
        "goals": ["Preserve glomerular filtration rate (e.g. maintain stable GFR)", "Control proteinuria"],
        "activities": [
            {"name": "Nephrotoxic Agent Avoidance", "detail": "Strictly avoid non-steroidal anti-inflammatory drugs (NSAIDs) like ibuprofen or naproxen."},
            {"name": "Renal Diet", "detail": "Reduce daily sodium intake (< 2g) and monitor protein intake to avoid hyperfiltration."},
            {"name": "Serum Chemistry Monitoring", "detail": "Perform basic metabolic panels (creatinine, potassium, eGFR) every 3 months."}
        ]
    },
    "lungs": {
        "title": "Chronic Respiratory Condition Management Plan",
        "description": "Pulmonary care plan for optimizing oxygenation and managing dyspnea.",
        "goals": ["Optimize spirometry metrics", "Prevent acute pulmonary exacerbations"],
        "activities": [
            {"name": "Inhaler Adherence Check", "detail": "Review correct metered-dose inhaler technique and verify daily compliance."},
            {"name": "Pulmonary Rehabilitation", "detail": "Perform pursed-lip breathing and diaphragmatic breathing exercises for 15 mins daily."},
            {"name": "Environmental Trigger Avoidance", "detail": "Eliminate exposure to tobacco smoke, dust, and particulate air pollutants."}
        ]
    },
    "liver": {
        "title": "Hepatic Protection and Monitoring Care Plan",
        "description": "Clinical care path designed to prevent progression of hepatic injury and cirrhosis.",
        "goals": ["Normalize serum transaminases (ALT/AST)", "Prevent portal hypertension complications"],
        "activities": [
            {"name": "Hepatoprotection", "detail": "Strictly avoid alcohol consumption and limit acetaminophen use to under 2g/day."},
            {"name": "Coagulation and Liver Panel", "detail": "Monitor Prothrombin Time (PT/INR) and serum albumin every 6 months."},
            {"name": "Abdominal Imaging Sweep", "detail": "Perform screening abdominal ultrasound every 6-12 months for surveillance."}
        ]
    },
    "stroke": {
        "title": "Secondary Stroke Prevention Care Plan",
        "description": "Neurovascular care plan focused on thromboembolic risk reduction and neuro-rehabilitation.",
        "goals": ["Prevent secondary ischemic events", "Optimize motor/sensory functional recovery"],
        "activities": [
            {"name": "Antiplatelet / Anticoagulant Therapy", "detail": "Verify strict daily adherence to prescribed aspirin, clopidogrel, or oral anticoagulants."},
            {"name": "Physical and Occupational Therapy", "detail": "Attend specialized physical rehabilitation sessions twice weekly."},
            {"name": "Lipid Lowering Optimization", "detail": "Implement high-intensity statin therapy to target aggressive plaque stabilization."}
        ]
    }
}

def generate_care_plan(patient_id: str, condition: str, severity: str = "moderate") -> Dict[str, Any]:
    """
    Generates a FHIR-compliant CarePlan resource based on patient conditions.
    """
    cond_key = condition.strip().lower()
    template = CARE_PLAN_TEMPLATES.get(cond_key)
    
    if not template:
        # Generic fallback care plan
        template = {
            "title": f"General Health Support Plan for {condition.capitalize()}",
            "description": "Standard diagnostic follow-up and monitoring plan.",
            "goals": ["Optimize wellness parameters", "Monitor disease progression"],
            "activities": [
                {"name": "Routine Follow-up", "detail": "Consult primary care physician in 30 days."},
                {"name": "General Diagnostics", "detail": "Undergo recommended age-appropriate screening evaluations."}
            ]
        }
        
    now_dt = datetime.now(timezone.utc)
    end_dt = now_dt + timedelta(days=180) # 6 months duration
    
    fhir_goals = []
    for i, g in enumerate(template["goals"]):
        fhir_goals.append({
            "id": f"goal-{i+1}",
            "description": {
                "text": g
            },
            "lifecycleStatus": "active"
        })
        
    fhir_activities = []
    for i, act in enumerate(template["activities"]):
        fhir_activities.append({
            "reference": {
                "display": act["name"]
            },
            "detail": {
                "kind": "Procedure",
                "status": "not-started",
                "doNotPerform": False,
                "description": act["detail"]
            }
        })
        
    return {
        "resourceType": "CarePlan",
        "id": f"plan-{cond_key}-{int(now_dt.timestamp())}",
        "status": "active",
        "intent": "plan",
        "title": template["title"],
        "description": template["description"],
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "period": {
            "start": fhir_datetime(now_dt),
            "end": fhir_datetime(end_dt)
        },
        "goal": fhir_goals,
        "activity": fhir_activities
    }
