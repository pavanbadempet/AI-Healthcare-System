"""
Unit tests for SOTA Zero Trust Security Engine (backend/sota_security_layer.py).
"""

from backend.sota_security_layer import ABACResource, ABACSubject, SOTASecurityLayerEngine


def test_abac_authorization_and_token_revocation():
    engine = SOTASecurityLayerEngine()

    # Token Revocation test
    token_id = "JWT_JTI_998877"
    assert engine.is_token_valid(token_id)
    engine.revoke_token(token_id)
    assert not engine.is_token_valid(token_id)

    # Standard Facility ABAC test
    clinician = ABACSubject(user_id="U_1001", role="CLINICIAN", facility_id="FAC_MAIN")
    res_normal = ABACResource(resource_id="REC_001", sensitivity="HIGH", owner_facility_id="FAC_MAIN")
    assert engine.authorize_access(clinician, res_normal)

    # Cross-facility restriction test
    res_other = ABACResource(resource_id="REC_002", sensitivity="HIGH", owner_facility_id="FAC_OTHER")
    assert not engine.authorize_access(clinician, res_other)

    # Break-Glass Emergency Override test
    emergency_nurse = ABACSubject(user_id="U_2002", role="NURSE", facility_id="FAC_MAIN", is_emergency=True)
    assert engine.authorize_access(emergency_nurse, res_other)
