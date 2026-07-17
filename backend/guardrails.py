"""AI Healthcare System — Input/Output Safety Guardrails.

Provides PII redaction, prompt injection detection, and input sanitization
to protect patient data and prevent adversarial misuse of AI features.
"""
import html
import re

# ---------------------------------------------------------------------------
# PII Detection Patterns
# ---------------------------------------------------------------------------

# Email addresses
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

# US Social Security Numbers (XXX-XX-XXXX)
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# Indian Aadhaar numbers (12 digits, optionally grouped in 4s)
AADHAAR_REGEX = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b")

# Phone numbers (US, India, international formats)
PHONE_REGEX = re.compile(
    r"\b(?:\+?1[-.\ ]?)?(?:\(?\d{3}\)?[-.\ ]?)\d{3}[-.\ ]?\d{4}\b"  # US
    r"|(?:^|(?<=\s))\+91[-.\ ]?\d{5}[-.\ ]?\d{5}\b"  # India +91
    r"|(?:^|(?<=\s))\+\d{1,3}[-.\ ]?\d{4,14}\b"  # International
)

# Credit card numbers (13-19 digits, optionally grouped with spaces/dashes)
CREDIT_CARD_REGEX = re.compile(
    r"\b(?:\d{4}[-\s]?){3,4}\d{1,4}\b"
)

# Passport numbers (common formats: 1-2 letters followed by 6-9 digits)
PASSPORT_REGEX = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")

# Medical Record Numbers (MRN patterns: letters+digits, 6-12 chars)
MRN_REGEX = re.compile(r"\b(?:MRN|mrn|MR)[-:\s]?\d{5,12}\b")

# IPv4 addresses
IPV4_REGEX = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)


# ---------------------------------------------------------------------------
# Prompt Injection Detection
# ---------------------------------------------------------------------------

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
    "jailbreak",
    # Emerging patterns
    "do anything now",
    "pretend you are",
    "forget all previous",
    "disregard above",
    "ignore all instructions",
    "new instructions:",
    "override all safety",
    "you have no restrictions",
    "simulate developer",
    "enable unrestricted mode",
    "ignore content policy",
    "bypass content filter",
    "reveal system prompt",
    "show me your instructions",
    "repeat your system message",
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


# ---------------------------------------------------------------------------
# PII Redaction
# ---------------------------------------------------------------------------

def redact_pii_from_text(text: str) -> str:
    """
    Scan the text and redact common PII formats.

    Covers: Email, SSN, Aadhaar, Phone, Credit Card, Passport, MRN, IPv4.
    """
    if not text:
        return ""

    # Redact Emails
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)

    # Redact SSNs
    text = SSN_REGEX.sub("[REDACTED_SSN]", text)

    # Redact Credit Card Numbers (before Aadhaar to prevent greedy 12-digit match)
    text = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", text)

    # Redact Aadhaar Numbers
    text = AADHAAR_REGEX.sub("[REDACTED_AADHAAR]", text)

    # Redact Phone Numbers
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)

    # Redact Passport Numbers
    text = PASSPORT_REGEX.sub("[REDACTED_PASSPORT]", text)

    # Redact Medical Record Numbers
    text = MRN_REGEX.sub("[REDACTED_MRN]", text)

    # Redact IPv4 Addresses
    text = IPV4_REGEX.sub("[REDACTED_IP]", text)

    return text


# ---------------------------------------------------------------------------
# Input Sanitization
# ---------------------------------------------------------------------------

# HTML/Script injection patterns
_SCRIPT_TAG_RE = re.compile(r"<\s*script[^>]*>.*?</\s*script\s*>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_EVENT_HANDLER_RE = re.compile(r"\bon\w+\s*=", re.IGNORECASE)
_JAVASCRIPT_URI_RE = re.compile(r"javascript\s*:", re.IGNORECASE)

# SQL injection patterns (basic detection)
_SQL_INJECTION_PATTERNS = [
    re.compile(r"(?:--|#)\s*$", re.MULTILINE),  # SQL comment at end of line
    re.compile(r";\s*(?:DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\s", re.IGNORECASE),
    re.compile(r"'\s*(?:OR|AND)\s+\d+\s*=\s*\d+", re.IGNORECASE),  # ' OR 1=1
    re.compile(r"UNION\s+(?:ALL\s+)?SELECT", re.IGNORECASE),
]


def sanitize_input(text: str) -> str:
    """
    Sanitize user input by stripping potentially dangerous content.

    - Removes script tags and HTML event handlers
    - Escapes remaining HTML entities
    - Does NOT alter clinical/medical content
    """
    if not text:
        return ""

    # Remove script tags entirely
    text = _SCRIPT_TAG_RE.sub("", text)

    # Remove HTML event handlers (onclick=, onerror=, etc.)
    text = _EVENT_HANDLER_RE.sub("", text)

    # Remove javascript: URIs
    text = _JAVASCRIPT_URI_RE.sub("", text)

    # Strip remaining HTML tags
    text = _HTML_TAG_RE.sub("", text)

    # Escape any remaining HTML entities for safe rendering
    text = html.unescape(text)

    return text.strip()


def contains_sql_injection(text: str) -> bool:
    """
    Detect potential SQL injection patterns in user input.
    Note: This is a defense-in-depth measure. SQLAlchemy parameterized queries
    are the primary protection against SQL injection.
    """
    if not text:
        return False
    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False
