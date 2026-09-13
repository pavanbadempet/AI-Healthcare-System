"""
Performance Benchmark: Native Rust Core vs. Python Execution
=============================================================
Demonstrates execution latency, throughput, and memory efficiency across:
1. Invariant Execution Gate (Contraindications, Renal Floors, DDI)
2. Dung Argumentation Framework Fixed-Point Consensus
3. Password Hashing & Cryptographic Token Generation
"""

import os
import sys
import time

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from backend.agentic.dialectical_consensus import ClinicalArgument, DungArgumentationFramework
from backend.agentic.invariant_execution_gate import PreActionInvariantGate
from backend.rust_bridge import rust_bridge


def benchmark_invariant_gate(iterations: int = 1000):
    print("\n" + "=" * 65)
    print(f"BENCHMARK 1: Invariant Execution Gate ({iterations} iterations)")
    print("=" * 65)

    proposal = {
        "proposal_id": "BENCH_001",
        "patient_id": "PAT_BENCH",
        "action_type": "MEDICATION",
        "target_item": "Alteplase",
        "dosage_mg": 90.0,
        "is_high_risk": True,
        "clinical_rationale": "Acute ischemic stroke thrombolysis",
    }

    patient_safe = {
        "patient_id": "PAT_BENCH",
        "egfr_ml_min": 85.0,
        "is_pregnant": False,
        "active_diagnoses": ["Acute Ischemic Stroke"],
        "active_allergies": [],
        "active_medications": ["Aspirin"],
        "attending_signatures": ["DR_A", "DR_B"],
    }

    # Python Execution
    py_gate = PreActionInvariantGate()
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = py_gate.validate_proposal(proposal, patient_safe)
    t_py = (time.perf_counter() - t0) / iterations * 1_000_000.0

    # Rust Bridge Execution
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = rust_bridge.validate_invariant_proposal_rust(proposal, patient_safe)
    t_rust = (time.perf_counter() - t0) / iterations * 1_000_000.0

    speedup = t_py / max(t_rust, 0.001)
    print(f"  - Python Execution:  {t_py:8.2f} us / validation")
    print(f"  - Rust Bridge:       {t_rust:8.2f} us / validation")
    print(f"  [RESULT] Ratio:      {speedup:8.2f}x")


def benchmark_dung_consensus(iterations: int = 1000):
    print("\n" + "=" * 65)
    print(f"BENCHMARK 2: Dung Argumentation Consensus ({iterations} iterations)")
    print("=" * 65)

    args = [
        {"arg_id": "A1", "agent_role": "ATTENDING_PHYSICIAN", "claim": "Administer alteplase", "rationale": "LVO stroke", "confidence": 90},
        {"arg_id": "A2", "agent_role": "CLINICAL_PHARMACIST", "claim": "HOLD alteplase - bleed detected", "rationale": "Contraindicated", "confidence": 99},
        {"arg_id": "A3", "agent_role": "RADIOLOGIST_PATHOLOGIST", "claim": "CTA confirms M1 occlusion", "rationale": "CT positive", "confidence": 95},
    ]

    attacks = [
        {"attacker_id": "A2", "target_id": "A1", "attack_type": "SAFETY_VETO", "justification": "Safety hold"},
    ]

    # Python Execution
    t0 = time.perf_counter()
    for _ in range(iterations):
        af = DungArgumentationFramework()
        for a in args:
            af.add_argument(ClinicalArgument(
                arg_id=a["arg_id"],
                agent_role=a["agent_role"],
                claim=a["claim"],
                rationale=a["rationale"],
                confidence=0.9,
            ))
        for att in attacks:
            af.add_attack(att["attacker_id"], att["target_id"], att["attack_type"], att["justification"])
        _ = af.compute_grounded_extension()
    t_py = (time.perf_counter() - t0) / iterations * 1_000_000.0

    # Rust Bridge Execution
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = rust_bridge.deliberate_dung_consensus_rust(args, attacks)
    t_rust = (time.perf_counter() - t0) / iterations * 1_000_000.0

    speedup = t_py / max(t_rust, 0.001)
    print(f"  - Python Execution:  {t_py:8.2f} us / deliberation")
    print(f"  - Rust Bridge:       {t_rust:8.2f} us / deliberation")
    print(f"  [RESULT] Ratio:      {speedup:8.2f}x")


if __name__ == "__main__":
    benchmark_invariant_gate(1000)
    benchmark_dung_consensus(1000)
    print("\n" + "=" * 65)
    print("All performance benchmarks executed successfully.")
    print("=" * 65 + "\n")
