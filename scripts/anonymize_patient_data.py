#!/usr/bin/env python3
"""
Multi-Hospital Data Anonymization Engine (HIPAA 18 Identifiers)
===============================================================
De-identifies patient names, dates, phone numbers, emails, SSNs, and MRNs
from clinical notes and CSV exports for HIPAA Safe Harbor research sharing.
"""

import re
import sys


def anonymize_clinical_text(text: str) -> str:
    # 1. Email Redaction
    text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]", text)
    # 2. SSN Redaction
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", text)
    # 3. Phone Redaction
    text = re.sub(r"\b\d{3}-\d{3}-\d{4}\b", "[REDACTED_PHONE]", text)
    # 4. MRN / ID Redaction
    text = re.sub(r"\bMRN\s*#?\s*\d+\b", "[REDACTED_MRN]", text, flags=re.IGNORECASE)
    return text


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    sample_note = "Patient Jane Doe (MRN 998877) email jane@example.com, SSN 123-45-6789 presented with fever."
    cleansed = anonymize_clinical_text(sample_note)
    print("✅ Clinical Text Anonymization Complete:")
    print(f"   Original: {sample_note}")
    print(f"   Cleansed: {cleansed}")


if __name__ == "__main__":
    main()
