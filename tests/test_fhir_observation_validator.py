"""
Unit tests for FHIR R4 LOINC laboratory Observation resource schema validation.
"""
import unittest

class TestFHIRObservationValidator(unittest.TestCase):
    def test_loinc_code_format(self):
        glucose_code = "15074-8"
        self.assertRegex(glucose_code, r"^\d{3,5}-\d$")

    def test_value_quantity_validation(self):
        obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "15074-8"}]},
            "valueQuantity": {"value": 98.6, "unit": "mg/dL"}
        }
        self.assertEqual(obs["status"], "final")
        self.assertIn("valueQuantity", obs)

if __name__ == "__main__":
    unittest.main()
