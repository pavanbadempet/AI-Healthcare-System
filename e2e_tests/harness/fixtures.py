"""
Test Data Fixtures and Factory generators for all 40 Healthcare System domains.
Provides valid baseline inputs and adversarial/boundary variations.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict


class TestDataFactory:
    """Generates realistic test payloads across all domains."""

    @staticmethod
    def user_create(username: str = None, role: str = "patient", email: str = None) -> Dict[str, Any]:
        tag = uuid.uuid4().hex[:6]
        u = username or f"user_{tag}"
        e = email or f"{u}@testdomain.org"
        return {
            "username": u,
            "email": e,
            "password": "StrongPassword123!",
            "full_name": "Test Patient",
            "dob": "1990-01-01",
        }

    @staticmethod
    def diabetes_input() -> Dict[str, Any]:
        return {
            "gender": 1,
            "age": 55.0,
            "hypertension": 1,
            "heart_disease": 0,
            "smoking_history": 1,
            "bmi": 28.5,
            "high_chol": 1,
            "physical_activity": 0,
            "general_health": 3,
        }

    @staticmethod
    def heart_input() -> Dict[str, Any]:
        return {
            "age": 60.0,
            "sex": 1,
            "cp": 2,
            "trestbps": 140.0,
            "chol": 240.0,
            "fbs": 0,
            "restecg": 1,
            "thalach": 150.0,
            "exang": 0,
            "oldpeak": 1.5,
            "slope": 1,
            "ca": 0,
            "thal": 2,
            "hdl": 45.0,
            "smoker": 1,
            "hyp_treatment": 1,
        }

    @staticmethod
    def kidney_input() -> Dict[str, Any]:
        return {
            "age": 58.0,
            "bp": 80.0,
            "sg": 1.020,
            "al": 1.0,
            "su": 0.0,
            "rbc": 1,
            "pc": 1,
            "pcc": 0,
            "ba": 0,
            "bgr": 121.0,
            "bu": 36.0,
            "sc": 1.2,
            "sod": 138.0,
            "pot": 4.4,
            "hemo": 15.4,
            "pcv": 44.0,
            "wc": 7800.0,
            "rc": 5.2,
            "htn": 1,
            "dm": 0,
            "cad": 0,
            "appet": 1,
            "pe": 0,
            "ane": 0,
        }

    @staticmethod
    def liver_input() -> Dict[str, Any]:
        return {
            "age": 45.0,
            "gender": 1,
            "total_bilirubin": 1.2,
            "direct_bilirubin": 0.4,
            "alkaline_phosphotase": 210.0,
            "alamine_aminotransferase": 35.0,
            "aspartate_aminotransferase": 40.0,
            "total_proteins": 6.8,
            "albumin": 3.5,
            "albumin_and_globulin_ratio": 1.0,
        }

    @staticmethod
    def lung_input() -> Dict[str, Any]:
        return {
            "gender": 1,
            "age": 62,
            "smoking": 2,
            "yellow_fingers": 2,
            "anxiety": 1,
            "peer_pressure": 1,
            "chronic_disease": 2,
            "fatigue": 2,
            "allergy": 1,
            "wheezing": 2,
            "alcohol_consuming": 2,
            "coughing": 2,
            "shortness_of_breath": 2,
            "swallowing_difficulty": 1,
            "chest_pain": 2,
        }

    @staticmethod
    def stroke_input() -> Dict[str, Any]:
        return {
            "gender": 1,
            "age": 67.0,
            "hypertension": 1,
            "heart_disease": 1,
            "ever_married": 1,
            "work_type": 2,
            "residence_type": 1,
            "avg_glucose_level": 228.69,
            "bmi": 36.6,
            "smoking_status": 2,
        }

    @staticmethod
    def facility_create() -> Dict[str, Any]:
        tag = uuid.uuid4().hex[:6]
        return {
            "name": f"St. Jude Medical Center {tag}",
            "address": "100 Healthcare Way, Metro City",
            "phone": "+1-555-0199",
            "license_number": f"HOSP-{tag.upper()}",
        }

    @staticmethod
    def department_create(facility_id: int = 1) -> Dict[str, Any]:
        tag = uuid.uuid4().hex[:6]
        return {
            "facility_id": facility_id,
            "name": f"Cardiology Department {tag}",
            "code": f"CARD-{tag.upper()}",
            "floor": "3rd Floor",
        }

    @staticmethod
    def bed_create(department_id: int = 1) -> Dict[str, Any]:
        tag = uuid.uuid4().hex[:4]
        return {
            "department_id": department_id,
            "bed_number": f"BED-{tag.upper()}",
            "room_number": f"ROOM-30{tag[:2]}",
            "bed_type": "icu",
            "status": "available",
        }

    @staticmethod
    def admission_create(patient_id: int = 1, bed_id: int = 1, department_id: int = 1) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "bed_id": bed_id,
            "department_id": department_id,
            "admission_reason": "Acute chest pain observation and telemetry",
            "notes": "Admitted via ED triage",
        }

    @staticmethod
    def encounter_create(patient_id: int = 1, doctor_id: int = 1, department_id: int = 1) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "department_id": department_id,
            "encounter_type": "inpatient",
            "reason": "Cardiology evaluation and ECG assessment",
        }

    @staticmethod
    def clinical_order_create(encounter_id: int = 1, patient_id: int = 1, doctor_id: int = 1) -> Dict[str, Any]:
        return {
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "order_type": "lab",
            "description": "Comprehensive Metabolic Panel and Troponin I",
            "priority": "stat",
        }

    @staticmethod
    def billable_service_create() -> Dict[str, Any]:
        tag = uuid.uuid4().hex[:4]
        return {
            "code": f"CPT-992{tag}",
            "name": "Level 4 Inpatient Medical Exam",
            "category": "evaluation_and_management",
            "base_price": 250.00,
            "description": "Comprehensive clinical consultation and diagnostic review",
        }

    @staticmethod
    def invoice_create(patient_id: int = 1, encounter_id: int = 1) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
            "items": [
                {
                    "description": "Inpatient Consultation",
                    "code": "CPT-99223",
                    "quantity": 1,
                    "unit_price": 250.00,
                },
                {
                    "description": "ECG 12-Lead Diagnostic",
                    "code": "CPT-93000",
                    "quantity": 1,
                    "unit_price": 85.00,
                },
            ],
            "notes": "Initial admission invoice",
        }

    @staticmethod
    def medication_inventory_create() -> Dict[str, Any]:
        tag = uuid.uuid4().hex[:4]
        return {
            "name": f"Metformin HCl {tag}",
            "generic_name": "Metformin",
            "ndc_code": f"00093-7212-{tag[:2]}",
            "dosage_form": "tablet",
            "strength": "500mg",
            "quantity_in_stock": 500,
            "reorder_level": 50,
            "unit_price": 0.45,
        }

    @staticmethod
    def prescription_create(patient_id: int = 1, doctor_id: int = 1) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "medication_name": "Metformin 500mg",
            "dosage": "500mg",
            "frequency": "twice daily with meals",
            "duration_days": 30,
            "quantity": 60,
            "instructions": "Take orally twice daily after meals",
        }

    @staticmethod
    def nursing_task_create(patient_id: int = 1, nurse_id: int = 1) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "nurse_id": nurse_id,
            "task_type": "vital_signs_check",
            "description": "Check blood pressure and pulse ox every 2 hours",
            "priority": "high",
        }

    @staticmethod
    def vitals_create(patient_id: int = 1) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "heart_rate": 78.0,
            "blood_pressure_systolic": 122.0,
            "blood_pressure_diastolic": 79.0,
            "respiratory_rate": 16.0,
            "temperature_celsius": 36.8,
            "oxygen_saturation": 98.5,
        }

    @staticmethod
    def appointment_create(patient_id: int = 1, doctor_id: int = 1) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "date": "2026-09-15",
            "time": "10:30:00",
            "reason": "Routine hypertension follow-up",
            "status": "scheduled",
        }
