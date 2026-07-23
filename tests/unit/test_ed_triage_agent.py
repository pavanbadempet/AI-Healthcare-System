"""
Unit tests for Emergency Department ED Triage Agent
"""

import pytest
from backend.agents.ed_triage_agent import EmergencyTriageAgent, ed_triage_agent


def test_evaluate_esi_level_1():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Unresponsive",
        heart_rate=160,
        systolic_bp=75,
        oxygen_sat=82,
        respiratory_rate=30,
        is_unresponsive_or_dying=True,
    )
    assert res["esi_level"] == 1
    assert res["acuity_category"] == "IMMEDIATE_RESUSCITATION"


def test_evaluate_esi_level_3():
    res = ed_triage_agent.evaluate_esi_triage(
        chief_complaint="Abdominal pain",
        heart_rate=88,
        systolic_bp=128,
        oxygen_sat=98,
        respiratory_rate=16,
        projected_resources_needed=2,
    )
    assert res["esi_level"] == 3
    assert res["acuity_category"] == "URGENT"
