"""
Unit tests for Prior Authorization Agent
"""

import pytest
from backend.agents.prior_authorization_agent import PriorAuthorizationAgent, prior_auth_agent


def test_generate_prior_auth_package_ready():
    res = prior_auth_agent.generate_prior_auth_package(
        patient_id=401,
        patient_name="Robert Taylor",
        requested_procedure_cpt="72148",  # Lumbar Spine MRI
        primary_icd10="M54.5",            # Low back pain
        clinical_justification="Patient has severe radicular low back pain with numbness for 8 weeks.",
        failed_conservative_therapies=["Physical Therapy 6 weeks", "NSAIDs"],
    )
    assert res["submission_status"] == "READY_FOR_SUBMISSION"
    assert res["has_sufficient_evidence"] is True
    assert "72148" in res["prior_auth_package_text"]


def test_generate_prior_auth_package_needs_doc():
    res = prior_auth_agent.generate_prior_auth_package(
        patient_id=402,
        patient_name="Mary Davis",
        requested_procedure_cpt="72148",
        primary_icd10="M54.5",
        clinical_justification="Back pain.",
        failed_conservative_therapies=[],
    )
    assert res["submission_status"] == "NEEDS_MORE_DOCUMENTATION"
    assert res["has_sufficient_evidence"] is False
