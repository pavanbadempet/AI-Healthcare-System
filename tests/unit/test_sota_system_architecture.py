"""
Unit tests for SOTA System Architectures (Hexagonal Ports/Adapters, EDA Backbone, Zero-Trust Multi-Tenancy).
"""

from backend.sota_system_architecture import (
    clinical_domain_service,
    event_driven_backbone,
    MultiTenantSecurityContext,
)

def test_hexagonal_architecture_ports_and_adapters():
    res = clinical_domain_service.process_triage("P-99", {"heart_rate": 115})
    assert res["patient_id"] == "P-99"
    assert res["triage_status"] == "HIGH_PRIORITY"

def test_event_driven_architecture_pubsub():
    received_events = []
    
    def on_vital_alert(event):
        received_events.append(event.payload["patient_id"])

    event_driven_backbone.subscribe("VITALS_ALERT", on_vital_alert)
    evt = event_driven_backbone.publish("VITALS_ALERT", {"patient_id": "P-404"})
    
    assert evt.event_id.startswith("SYS-")
    assert "P-404" in received_events

def test_zero_trust_multi_tenant_isolation():
    ctx = MultiTenantSecurityContext(
        tenant_id="HOSPITAL-A",
        user_id="U-100",
        user_role="PHYSICIAN",
        token_signature="SIG-123"
    )
    
    assert ctx.authorize_tenant_access("HOSPITAL-A") is True
    assert ctx.authorize_tenant_access("HOSPITAL-B") is False
