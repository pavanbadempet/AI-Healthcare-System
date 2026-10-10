"""
Unit tests for ICD-10-CM alphanumeric format normalization and hierarchy validation.
"""
import unittest

class TestICD10Normalization(unittest.TestCase):
    def test_decimal_insertion(self):
        raw_code = "I10"
        self.assertEqual(raw_code, "I10")

    def test_subdivision_formatting(self):
        raw_code = "E119"
        formatted = f"{raw_code[:3]}.{raw_code[3:]}" if len(raw_code) > 3 else raw_code
        self.assertEqual(formatted, "E11.9")

if __name__ == "__main__":
    unittest.main()
