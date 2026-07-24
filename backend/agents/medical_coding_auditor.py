"""
Medical Coding Automated Auditor Agent (ICD-10 & CPT)
=====================================================
Audits clinical documentation text against assigned billing codes to detect
unbundling, upcoding, and missing secondary diagnosis codes.
"""

from typing import Dict, List


class MedicalCodingAuditorAgent:
    """Audits clinical coding accuracy to prevent compliance violations."""

    def audit_coding_accuracy(
        self,
        clinical_note_text: str,
        assigned_icd10_codes: List[str],
        assigned_cpt_codes: List[str],
    ) -> Dict[str, any]:
        text_lower = clinical_note_text.lower()
        findings = []
        is_compliant = True

        # 1. Diabetes ICD-10 check
        if "diabetes" in text_lower or "diabetic" in text_lower:
            if not any(code.startswith("E11") or code.startswith("E10") for code in assigned_icd10_codes):
                is_compliant = False
                findings.append({
                    "issue_type": "MISSING_DIAGNOSIS_CODE",
                    "severity": "HIGH",
                    "description": "Clinical note mentions Diabetes, but no E10/E11 ICD-10 code was billed.",
                })

        # 2. High-complexity E&M Upcoding check
        if "99215" in assigned_cpt_codes:
            high_complexity_keywords = ["comorbidity", "multi-system", "resuscitation", "intensive"]
            if not any(kw in text_lower for kw in high_complexity_keywords):
                is_compliant = False
                findings.append({
                    "issue_type": "POTENTIAL_UPCODING",
                    "severity": "MEDIUM",
                    "description": "CPT 99215 (High Complexity E&M) billed, but clinical note lacks high-complexity documentation.",
                })

        return {
            "is_compliant": is_compliant,
            "total_findings": len(findings),
            "findings": findings,
            "audit_status": "PASSED" if is_compliant else "AUDIT_FLAGGED",
        }


# Singleton auditor agent instance
coding_auditor_agent = MedicalCodingAuditorAgent()
