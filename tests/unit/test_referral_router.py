"""
Unit tests for Clinical Referral Router Agent
"""

import pytest
from backend.agents.referral_router_agent import ClinicalReferralRouterAgent, referral_router_agent


def test_route_referral_nephrology():
    res = referral_router_agent.route_referral(
        patient_id=301,
        primary_complaint="Elevated serum creatinine and CKD stage 3",
        icd10_codes=["N18.3"],
        urgency_level="URGENT",
    )
    assert res["target_specialty"] == "NEPHROLOGY"
    assert res["max_wait_days"] == 7
    assert res["routing_status"] == "REFERRAL_ROUTED"


def test_route_referral_general():
    res = referral_router_agent.route_referral(
        patient_id=302,
        primary_complaint="Annual wellness checkup",
        icd10_codes=[],
        urgency_level="ROUTINE",
    )
    assert res["target_specialty"] == "GENERAL_INTERNAL_MEDICINE"
    assert res["max_wait_days"] == 30
