import re

# Regular expressions for PII detection
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Aadhaar number regex: 12 digits (often grouped in 4s with spaces)
AADHAAR_REGEX = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b")

# Keywords that indicate prompt injection
INJECTION_KEYWORDS = [
    "ignore prior instructions",
    "ignore previous instructions",
    "override safety rules",
    "system override",
    "you are now a doctor",
    "you can prescribe",
    "bypass safety",
    "act as an unrestricted",
    "ignore system prompt",
    "developer mode",
    "jailbreak"
]

def is_prompt_injection(text: str) -> bool:
    """
    Check if the input text contains typical prompt injection attempts or system override instructions.
    """
    if not text:
        return False
    text_lower = text.lower()
    for keyword in INJECTION_KEYWORDS:
        if keyword in text_lower:
            return True
    return False

def redact_pii_from_text(text: str) -> str:
    """
    Scan the text and redact common PII formats (Aadhaar, SSN, and Email).
    """
    if not text:
        return ""

    # Redact Emails
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)

    # Redact SSNs
    text = SSN_REGEX.sub("[REDACTED_SSN]", text)

    # Redact Aadhaar Numbers
    text = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", text)

    return text
