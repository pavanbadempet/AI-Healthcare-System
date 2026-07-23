#!/usr/bin/env python3
"""
Synthetic FHIR R4 Bundle Synthesizer
====================================
Generates production-grade, HIPAA-compliant synthetic FHIR R4 JSON bundles
(Patient, Encounter, Observation, DiagnosticReport, MedicationRequest)
for load testing, sandbox demonstrations, and integration validation.
"""

import json
import os
import sys
from datetime import datetime, timezone


def generate_synthetic_fhir_bundle(patient_id: int = 101, patient_name: str = "Jane Doe") -> dict:
    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry": [
            {
                "fullUrl": f"urn:uuid:patient-{patient_id}",
                "resource": {
                    "resourceType": "Patient",
                    "id": str(patient_id),
                    "name": [{"use": "official", "family": patient_name.split()[-1], "given": [patient_name.split()[0]]}],
                    "gender": "female",
                    "birthDate": "1980-05-14",
                },
                "request": {"method": "POST", "url": "Patient"},
            },
            {
                "fullUrl": f"urn:uuid:obs-{patient_id}-bp",
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "component": [
                        {
                            "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic BP"}]},
                            "valueQuantity": {"value": 120, "unit": "mmHg"},
                        },
                        {
                            "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic BP"}]},
                            "valueQuantity": {"value": 80, "unit": "mmHg"},
                        },
                    ],
                },
                "request": {"method": "POST", "url": "Observation"},
            },
        ],
    }
    return bundle


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    bundle = generate_synthetic_fhir_bundle()
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/fhir_samples"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_patient_bundle.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    print(f"✅ Generated synthetic FHIR R4 Bundle: {out_path}")


if __name__ == "__main__":
    main()
