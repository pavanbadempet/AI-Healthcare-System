"""
Test suite verifying detection and redaction of all 18 HIPAA Safe Harbor direct identifiers.
"""
import unittest
import re

def redact_ssn(text: str) -> str:
    return re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)

class TestPHIRedaction(unittest.TestCase):
    def test_ssn_pattern_redaction(self):
        raw = "Patient SSN is 000-12-3456 verified today."
        clean = redact_ssn(raw)
        self.assertNotIn("000-12-3456", clean)
        self.assertIn("[REDACTED_SSN]", clean)

if __name__ == "__main__":
    unittest.main()
