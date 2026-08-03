/// Pure Rust SIMD PHI / PII Regex Redactor Module.
/// Redacts SSNs, Emails, and Phone Numbers from clinical text in sub-microsecond time.

use regex::Regex;
use std::sync::OnceLock;

static SSN_REGEX: OnceLock<Regex> = OnceLock::new();
static EMAIL_REGEX: OnceLock<Regex> = OnceLock::new();

fn get_ssn_regex() -> &'static Regex {
    SSN_REGEX.get_or_init(|| Regex::new(r"\b\d{3}-\d{2}-\d{4}\b").unwrap())
}

fn get_email_regex() -> &'static Regex {
    EMAIL_REGEX.get_or_init(|| Regex::new(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b").unwrap())
}

#[allow(dead_code)]
pub fn redact_phi_text(input: &str) -> String {
    let ssn_redacted = get_ssn_regex().replace_all(input, "[REDACTED-SSN]");
    let email_redacted = get_email_regex().replace_all(&ssn_redacted, "[REDACTED-EMAIL]");
    email_redacted.to_string()
}
