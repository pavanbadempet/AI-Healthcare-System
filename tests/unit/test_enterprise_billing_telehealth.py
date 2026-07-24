from backend.claims import CMS1500Claim
from backend.claims_denial import analyse_denial_risk
from backend.telehealth import TelehealthSession

# ── CMS-1500 Claims & Claims Denial Predictor Tests ────────────────────────

def test_claims_preflight_passed():
    # Valid claim matching CPT 93000 (ECG) with Circulatory/Heart ICD-10 (I25.10)
    claim = CMS1500Claim(
        claim_id="claim-001",
        patient_name="John Doe",
        insurance_id="INS-7788",
        provider_name="Dr. Alice Smith",
        provider_npi="1234567890", # Valid 10-digit
        provider_tax_id="TX-556677",
        diagnoses=["I25.10", "E11.9"],
        procedures=[
            {"cpt": "93000", "charge": 150.00, "date": "2026-07-16", "units": 1, "diagnosis_pointer": [1]}
        ],
        place_of_service="11"
    )

    assert claim.calculate_total_charge() == 150.00

    analysis = analyse_denial_risk(claim)
    assert analysis["denial_risk"] == "LOW"
    assert analysis["passed_preflight"] is True
    assert len(analysis["warnings"]) == 0


def test_claims_denial_medium_risk_mismatch():
    # Mismatch: CPT 50200 (Renal biopsy) paired with a Heart diagnosis (I25.10)
    claim = CMS1500Claim(
        claim_id="claim-002",
        patient_name="John Doe",
        insurance_id="INS-7788",
        provider_name="Dr. Alice Smith",
        provider_npi="1234567890",
        provider_tax_id="TX-556677",
        diagnoses=["I25.10"], # Heart only, no renal "N" diagnosis
        procedures=[
            {"cpt": "50200", "charge": 800.00, "date": "2026-07-16", "units": 1, "diagnosis_pointer": [1]}
        ]
    )

    analysis = analyse_denial_risk(claim)
    assert analysis["denial_risk"] == "MEDIUM"
    assert analysis["passed_preflight"] is False
    assert any("CPT 50200 Mismatch" in w for w in analysis["warnings"])


def test_claims_denial_high_risk_missing_npi():
    claim = CMS1500Claim(
        claim_id="claim-003",
        patient_name="John Doe",
        insurance_id="INS-7788",
        provider_name="Dr. Alice Smith",
        provider_npi="abc", # Invalid NPI
        provider_tax_id="TX-556677",
        diagnoses=["I25.10"],
        procedures=[
            {"cpt": "93000", "charge": 150.00, "date": "2026-07-16"}
        ]
    )

    analysis = analyse_denial_risk(claim)
    assert analysis["denial_risk"] == "HIGH"
    assert analysis["passed_preflight"] is False
    assert any("NPI must be exactly a 10-digit" in w for w in analysis["warnings"])


# ── Telehealth Session Orchestration Tests ─────────────────────────────────

def test_telehealth_session_flow():
    session = TelehealthSession(
        session_id="session-webrtc-99",
        patient_id="patient-44",
        provider_id="provider-88",
        room_name="Consult-Room-99"
    )

    assert session.status == "scheduled"

    session.start_session()
    assert session.status == "active"
    assert session.started_at is not None

    # Verify WebRTC signaling tokens
    token_info = session.generate_webrtc_token(user_id="patient-44", role="patient")
    assert token_info["room_name"] == "Consult-Room-99"
    assert token_info["role"] == "patient"
    assert token_info["token_type"] == "Bearer WebRTC-Signaling"
    assert token_info["access_token"].startswith("jwt-webrtc-")

    # Audit call stats
    quality = session.audit_quality_metrics(packet_loss=0.2, latency_ms=45.0)
    assert quality["quality_rating"] == "EXCELLENT"

    quality_poor = session.audit_quality_metrics(packet_loss=6.5, latency_ms=300.0)
    assert quality_poor["quality_rating"] == "POOR"

    session.end_session(duration_minutes=42.5)
    assert session.status == "completed"
    assert session.duration_minutes == 42.5

def test_claims_denial_telemedicine_modifier_missing():
    # Telehealth place of service "02" with CPT 90837 but missing required modifier (95, GT, GQ)
    claim = CMS1500Claim(
        claim_id="claim-tele-001",
        patient_name="Jane Doe",
        insurance_id="INS-9988",
        provider_name="Dr. Smith",
        provider_npi="1234567890",
        provider_tax_id="TX-556677",
        diagnoses=["F32.9"],
        procedures=[
            {"cpt": "90837", "charge": 200.00, "date": "2026-07-16", "modifiers": []}
        ],
        place_of_service="02"
    )

    analysis = analyse_denial_risk(claim)
    assert analysis["denial_risk"] == "MEDIUM"
    assert analysis["passed_preflight"] is False
    assert any("requires a telemedicine modifier" in w for w in analysis["warnings"])

