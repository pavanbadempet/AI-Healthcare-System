import json
import logging

from sqlalchemy.orm import Session

from backend.agents.base_agent import BaseAgent
from backend.core_ai import generate
from backend.prompt_registry import get_prompt

logger = logging.getLogger(__name__)

class ClinicalBillingAgent(BaseAgent):
    """
    State-of-the-Art (SOTA) Medical Billing and Claims Denial Agent.
    Audits clinical notes (SOAP notes), recommends optimal ICD-10 and CPT codes,
    and predicts claims denial risk with recommendations for corrections.
    """

    def __init__(self, db: Session, name: str = "Clinical Billing Auditor"):
        super().__init__(name)
        self.db = db

    async def audit_billing_claim(self, soap_note: str) -> dict:
        """
        Audits a clinical SOAP note for ICD-10/CPT coding suitability and denial risk assessment.
        """
        self.start()

        if not soap_note or not soap_note.strip():
            self.log_error("SOAP note is empty.")
            self.finish("failed")
            return {"error": "SOAP note is empty."}

        self.log_step("Audit Billing Claim", "Calling SOTA Billing Auditor LLM...")
        prompt = get_prompt("clinical_billing_audit").format(
            soap_note=soap_note
        )
        self.estimate_tokens(prompt)
        raw_output = await generate(
            prompt=prompt,
            system="You are an expert clinical billing auditor specializing in HIPAA compliance, ICD-10/CPT coding, and claims denial mitigation."
        )
        self.estimate_tokens(raw_output, is_output=True)

        try:
            # Clean raw output from any markdown block formatting
            clean_str = raw_output.strip()
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()

            structured_report = json.loads(clean_str)
            self.log_step("Parse JSON Response", "Successfully parsed structured billing audit report.")
            self.finish("completed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "data": structured_report
            }
        except Exception as e:
            logger.warning("Failed to parse billing audit output as JSON: %s", e)
            self.log_error(f"JSON parsing failed: {str(e)}")
            fallback = {
                "icd10_codes": [],
                "cpt_codes": [],
                "denial_risk": "HIGH",
                "warnings": [f"Failed to parse structured audit report: {str(e)}"],
                "recommendations": ["Review clinical note manually; model output was not valid JSON."]
            }
            self.finish("failed")
            return {
                "telemetry": {
                    "duration": self.duration,
                    "input_tokens": self.input_tokens_estimated,
                    "output_tokens": self.output_tokens_estimated,
                    "estimated_cost": self.estimated_cost
                },
                "data": fallback
            }
