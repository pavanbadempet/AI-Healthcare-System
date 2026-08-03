"""
Unit tests for eBPF Kernel Socket Filter and Autonomous Clinical Multi-Agent Swarm.
"""

from backend.ebpf_kernel_filter import ebpf_engine, EBPFPacketHeader
from backend.clinical_agent_swarm import clinical_agent_swarm_engine, ClinicalSwarmInput

def test_ebpf_kernel_filter_evaluation():
    # 1. Valid packet on port 8000
    valid_pkt = EBPFPacketHeader(source_ip="127.0.0.1", destination_port=8000, payload_size_bytes=1024)
    res = ebpf_engine.evaluate_packet(valid_pkt)
    assert res.status == "ALLOWED"
    assert res.action == "PASS_FAST_PATH"
    assert res.kernel_latency_ns > 0

    # 2. Blocked packet on unauthorized port
    invalid_pkt = EBPFPacketHeader(source_ip="10.0.0.5", destination_port=22, payload_size_bytes=512)
    res_drop = ebpf_engine.evaluate_packet(invalid_pkt)
    assert res_drop.status == "DENIED"
    assert res_drop.action == "DROP_UNAUTHORIZED_PORT"

def test_clinical_agent_swarm_orchestration():
    swarm_input = ClinicalSwarmInput(
        patient_id="PATIENT-TEST-100",
        chief_complaint="Chest pain and dizziness",
        vitals={"bp": "150/95", "hr": 110, "spo2": 92},
        current_medications=["Warfarin", "Aspirin"]
    )
    result = clinical_agent_swarm_engine.process_patient(swarm_input)
    assert result.triage_level == "EMERGENCY_LEVEL_1"
    assert len(result.agent_assessments) == 3
    assert len(result.contraindications_flagged) > 0
    assert len(result.react_reasoning_trace) >= 2
    assert result.react_reasoning_trace[0].action_tool == "rust_gateway_ffi.calculate_egfr_py"
    assert "Warfarin + Aspirin" in result.contraindications_flagged[0]
    assert "CLINICAL SUMMARY FOR PATIENT-TEST-100" in result.discharge_summary_draft
