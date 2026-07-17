from typing import Any, Dict, List


class CMS1500Claim:
    def __init__(
        self,
        claim_id: str,
        patient_name: str,
        insurance_id: str,
        provider_name: str,
        provider_npi: str,
        provider_tax_id: str,
        diagnoses: List[str],
        procedures: List[Dict[str, Any]],
        place_of_service: str = "11"
    ):
        self.claim_id = claim_id
        self.patient_name = patient_name
        self.insurance_id = insurance_id
        self.provider_name = provider_name
        self.provider_npi = provider_npi
        self.provider_tax_id = provider_tax_id
        self.diagnoses = diagnoses[:12]
        self.procedures = procedures
        self.place_of_service = place_of_service

    def calculate_total_charge(self) -> float:
        return sum(float(proc.get("charge", 0.0)) for proc in self.procedures)

    def to_json_payload(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "insurer_info": {
                "program_type": "commercial"
            },
            "patient_info": {
                "name": self.patient_name,
                "insurance_policy_id": self.insurance_id
            },
            "provider_info": {
                "name": self.provider_name,
                "npi": self.provider_npi,
                "tax_id": self.provider_tax_id
            },
            "billing_details": {
                "place_of_service": self.place_of_service,
                "diagnoses": self.diagnoses,
                "service_lines": [
                    {
                        "date_of_service": str(proc.get("date")),
                        "cpt_hcpcs": proc.get("cpt"),
                        "diagnosis_pointer": proc.get("diagnosis_pointer", [1]),
                        "charges": float(proc.get("charge", 0.0)),
                        "units": int(proc.get("units", 1))
                    }
                    for proc in self.procedures
                ],
                "total_charge": self.calculate_total_charge()
            }
        }
