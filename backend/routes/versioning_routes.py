"""FastAPI Router for Level 13 Clinical Version Control, Care Protocol Branching & Simulation OS."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.routes.history_routes import event_store as history_event_store
from backend.schemas.versioning import (
    AttestationResponse,
    AttestInferenceRequest,
    BranchResponse,
    BranchStateResponse,
    CreateBranchRequest,
    CreateProtocolRequest,
    MergeBranchRequest,
    MergeBranchResponse,
    MutateBranchRequest,
    ProtocolDiffResponse,
    ProtocolResponse,
    RegisterTriadRequest,
    ScanDeprecationsResponse,
    TransitionProtocolRequest,
    TriadResponse,
    VerifyProvenanceResponse,
    VersioningHealthResponse,
)
from backend.versioning.chart_branch_engine import ChartBranchEngine
from backend.versioning.ontology_version_engine import OntologyVersionEngine
from backend.versioning.protocol_vcs import ProtocolVCSEngine
from backend.versioning.triad_lineage_registry import ModelDataTriadRegistry

logger = logging.getLogger("backend.versioning")

router = APIRouter(
    prefix="/v1/versioning",
    tags=["Clinical Version Control & Simulation"],
)

# Global engine singletons
branch_engine = ChartBranchEngine(event_store=history_event_store)
protocol_engine = ProtocolVCSEngine()
triad_registry = ModelDataTriadRegistry()
ontology_engine = OntologyVersionEngine()


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime.datetime]:
    if not dt_str:
        return None
    try:
        clean = dt_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(clean)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISO 8601 timestamp: '{dt_str}'. Error: {exc}",
        ) from exc


# =========================================================================
# 1. Patient Record Branching & Simulation Workspaces
# =========================================================================

@router.post("/branches/create", response_model=BranchResponse)
def create_simulation_branch(req: CreateBranchRequest) -> BranchResponse:
    """Fork a live patient chart into an isolated Copy-on-Write simulation branch."""
    meta = branch_engine.create_branch(
        patient_id=req.patient_id,
        branch_name=req.branch_name,
        author_id=req.author_id,
        author_name=req.author_name,
        purpose=req.purpose,
    )
    return BranchResponse(**meta.to_dict())


@router.post("/branches/{branch_id}/mutate")
def mutate_simulation_branch(branch_id: str, req: MutateBranchRequest) -> Dict[str, Any]:
    """Record a simulated medication order or clinical action in an active branch."""
    v_time = _parse_iso(req.valid_time)
    try:
        ev = branch_engine.mutate_branch(
            branch_id=branch_id,
            event_type=req.event_type,
            payload=req.payload,
            valid_time=v_time,
        )
        return ev.to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/branches/{branch_id}/state", response_model=BranchStateResponse)
def get_branch_simulated_state(branch_id: str) -> BranchStateResponse:
    """Retrieve the projected hypothetical patient chart within a simulation branch."""
    try:
        state = branch_engine.get_branch_state(branch_id)
        return BranchStateResponse(
            branch_id=state["branch_id"],
            patient_id=state["patient_id"],
            branch_name=state["branch_name"],
            simulated_event_count=state["simulated_event_count"],
            conditions=state.get("conditions", {}),
            medications=state.get("medications", {}),
            vitals=state.get("vitals", []),
            allergies=state.get("allergies", {}),
            labs=state.get("labs", {}),
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/branches/{branch_id}/merge", response_model=MergeBranchResponse)
def merge_branch_to_trunk(branch_id: str, req: MergeBranchRequest) -> MergeBranchResponse:
    """Perform 3-way merge between base snapshot, current live trunk, and branch."""
    try:
        result = branch_engine.three_way_merge(
            branch_id=branch_id,
            merging_clinician_id=req.merging_clinician_id,
            merging_clinician_name=req.merging_clinician_name,
            allow_conflict_override=req.allow_conflict_override,
        )
        return MergeBranchResponse(**result)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/patient/{patient_id}/branches", response_model=List[BranchResponse])
def list_patient_simulation_branches(patient_id: str) -> List[BranchResponse]:
    """List all simulation branches created for a given patient."""
    branches = branch_engine.list_patient_branches(patient_id)
    return [BranchResponse(**b.to_dict()) for b in branches]


# =========================================================================
# 2. Care Protocol & Order Set Version Control
# =========================================================================

@router.post("/protocols/create", response_model=ProtocolResponse)
def create_clinical_protocol(req: CreateProtocolRequest) -> ProtocolResponse:
    """Create a new clinical protocol version under SemVer governance."""
    try:
        proto = protocol_engine.create_protocol(
            protocol_id=req.protocol_id,
            title=req.title,
            version_str=req.version,
            steps_data=req.steps,
            author_id=req.author_id,
        )
        return ProtocolResponse(**proto.to_dict())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/protocols/{protocol_id}/transition", response_model=ProtocolResponse)
def transition_protocol_status(protocol_id: str, req: TransitionProtocolRequest) -> ProtocolResponse:
    """Transition protocol through approval lifecycle stages with safety linter checks."""
    try:
        proto = protocol_engine.transition_status(
            protocol_id=protocol_id,
            version_str=req.version,
            target_status=req.target_status,
            user_id=req.user_id,
            canary_units=req.canary_units,
        )
        return ProtocolResponse(**proto.to_dict())
    except (KeyError, ValueError) as exc:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(exc, KeyError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/protocols/{protocol_id}/effective", response_model=ProtocolResponse)
def get_effective_protocol(
    protocol_id: str,
    unit: Optional[str] = Query(None, description="Hospital ward / unit (e.g. NEURO_ICU)"),
) -> ProtocolResponse:
    """Resolve the active or canary protocol version governing a specific hospital unit."""
    proto = protocol_engine.resolve_effective_protocol(protocol_id=protocol_id, unit_name=unit)
    if not proto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active or canary protocol resolved for '{protocol_id}'",
        )
    return ProtocolResponse(**proto.to_dict())


@router.get("/protocols/{protocol_id}/diff", response_model=ProtocolDiffResponse)
def diff_protocol_versions(
    protocol_id: str,
    v1: str = Query(..., description="Baseline version string"),
    v2: str = Query(..., description="Comparison version string"),
) -> ProtocolDiffResponse:
    """Compute structural delta between two protocol versions."""
    try:
        delta = protocol_engine.diff_protocols(protocol_id=protocol_id, version_v1=v1, version_v2=v2)
        return ProtocolDiffResponse(**delta)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# =========================================================================
# 3. Model-Data-Code Triad Cryptographic Provenance
# =========================================================================

@router.post("/triad/register", response_model=TriadResponse)
def register_model_data_triad(req: RegisterTriadRequest) -> TriadResponse:
    """Register an immutable Model-Data-Code triad with HMAC provenance seal."""
    triad = triad_registry.register_triad(
        model_id=req.model_id,
        weights_digest=req.weights_digest,
        dataset_digest=req.dataset_digest,
        code_commit_hash=req.code_commit_hash,
        framework=req.framework,
        metadata=req.metadata,
    )
    return TriadResponse(**triad.to_dict())


@router.post("/triad/attest", response_model=AttestationResponse)
def attest_ai_inference(req: AttestInferenceRequest) -> AttestationResponse:
    """Issue a cryptographically sealed inference attestation certificate."""
    try:
        att = triad_registry.attest_inference(
            patient_id=req.patient_id,
            prediction_id=req.prediction_id,
            triad_id=req.triad_id,
            input_features=req.input_features,
            output_prediction=req.output_prediction,
        )
        return AttestationResponse(**att.to_dict())
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/triad/verify/{attestation_id}", response_model=VerifyProvenanceResponse)
def verify_inference_provenance(attestation_id: str) -> VerifyProvenanceResponse:
    """Verify cryptographic provenance and tamper-free lineage for a prediction certificate."""
    try:
        result = triad_registry.verify_provenance(attestation_id)
        return VerifyProvenanceResponse(**result)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# =========================================================================
# 4. Semantic Ontology Deprecation Scanner
# =========================================================================

@router.post("/patient/{patient_id}/scan-deprecations", response_model=ScanDeprecationsResponse)
def scan_chart_for_deprecations(
    patient_id: str,
    target_release: str = Query("2026-06", description="Target ontology release version"),
) -> ScanDeprecationsResponse:
    """Inspect patient chart for retired or superseded medical concepts and generate migration patch."""
    chart = history_event_store.project_patient_chart(patient_id=patient_id)
    findings = ontology_engine.scan_chart_for_deprecations(chart=chart, target_release=target_release)
    patch = ontology_engine.generate_migration_patch(chart=chart, findings=findings) if findings else None

    return ScanDeprecationsResponse(
        patient_id=patient_id,
        target_release=target_release,
        findings=[f.to_dict() for f in findings],
        migration_patch=patch,
    )


# =========================================================================
# 5. Operational Status Check
# =========================================================================

@router.get("/health", response_model=VersioningHealthResponse)
def get_versioning_health() -> VersioningHealthResponse:
    """Operational health check for the Clinical Version Control & Simulation OS."""
    active_b = sum(1 for b in branch_engine._branches.values() if b.status == "ACTIVE")
    protos = len(protocol_engine._protocols)
    triads = len(triad_registry._triads)

    return VersioningHealthResponse(
        status="HEALTHY",
        engine="CLINICAL_VCS_SIMULATION_OS",
        active_branches=active_b,
        registered_protocols=protos,
        model_triads=triads,
    )
