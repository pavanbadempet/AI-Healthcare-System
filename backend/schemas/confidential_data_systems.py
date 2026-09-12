"""
Pydantic Schemas for Level 7 Theoretical Peak & Confidential Data Systems:
- Learned Index Structures (PGM-Index & Learned CDFs)
- Confidential Clean-Room Remote Attestation & Hardware Enclave Verification
- Autonomous Adaptive Join Optimizer & Physical Access Planner
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Learned Index Schemas (PGM-Index)
# ---------------------------------------------------------------------------

class LearnedIndexBuildRequest(BaseModel):
    keys: List[float] = Field(..., description="Numeric keys to index (timestamps, patient IDs, lab values)")
    epsilon: int = Field(default=16, description="Strict maximum error bound per segment")


class LearnedIndexBuildResponse(BaseModel):
    num_records: int = Field(..., description="Total indexed records")
    epsilon: int = Field(..., description="Configured error bound")
    num_levels: int = Field(..., description="Hierarchical model depth")
    total_segments: int = Field(..., description="Total linear segments across all levels")
    base_level_segments: int = Field(..., description="Segments in level 0")
    pgm_index_size_bytes: int = Field(..., description="Memory footprint of learned index in bytes")
    estimated_btree_size_bytes: int = Field(..., description="Estimated B+ tree footprint in bytes")
    memory_compression_ratio: float = Field(..., description="Footprint reduction ratio vs B-tree")
    build_time_ms: float = Field(..., description="Model construction duration in milliseconds")


class LearnedIndexQueryRequest(BaseModel):
    key: float = Field(..., description="Key to look up")


class LearnedIndexQueryResponse(BaseModel):
    found: bool = Field(..., description="Whether key exists in dataset")
    position: Optional[int] = Field(default=None, description="Index position of key if found")
    predicted_position: Optional[float] = Field(default=None, description="Model-predicted position")
    error_window_size: int = Field(..., description="Bounded search range evaluated")
    latency_us: float = Field(..., description="Query lookup latency in microseconds")


class LearnedIndexRangeRequest(BaseModel):
    min_key: float = Field(..., description="Range lower bound")
    max_key: float = Field(..., description="Range upper bound")


class LearnedIndexRangeResponse(BaseModel):
    count: int = Field(..., description="Number of matching records")
    matched_indices: List[int] = Field(..., description="Matching record positions")
    latency_us: float = Field(..., description="Range query latency in microseconds")


# ---------------------------------------------------------------------------
# 2. Confidential Clean Room & Hardware Enclave Schemas
# ---------------------------------------------------------------------------

class EnclaveAttestRequest(BaseModel):
    architecture: str = Field(default="AMD_SEV_SNP", description="TEE architecture (AMD_SEV_SNP, INTEL_TDX, AWS_NITRO)")
    image_tag: str = Field(default="CLINICAL_ANALYTICS_V1", description="Registered enclave image identifier")
    client_ephemeral_pubkey: str = Field(..., description="Client ephemeral ECDH session public key")


class EnclaveAttestResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether attestation passed all cryptographic checks")
    architecture: str = Field(..., description="TEE architecture")
    mrenclave_verified: bool = Field(..., description="Enclave binary hash verification")
    pcr_integrity_verified: bool = Field(..., description="Platform boot registers verification")
    key_binding_verified: bool = Field(..., description="Ephemeral session key binding in report_data")
    hardware_pki_verified: bool = Field(..., description="Vendor root-of-trust signature verification")
    enclave_session_id: str = Field(..., description="Authenticated enclave session handle")
    verdict_message: str = Field(..., description="Detailed attestation verdict")
    quote_id: str = Field(..., description="Attestation quote identifier")


class CleanRoomComputeRequest(BaseModel):
    enclave_session_id: str = Field(..., description="Active attested enclave session handle")
    hospital_a_dataset: List[Dict[str, Any]] = Field(..., description="Confidential records from Hospital Alpha")
    hospital_b_dataset: List[Dict[str, Any]] = Field(..., description="Confidential records from Hospital Beta")
    computation_type: str = Field(default="FEDERATED_COHORT_ANALYTICS", description="Clean-room algorithm to execute")


class CleanRoomComputeResponse(BaseModel):
    enclave_session_id: str = Field(..., description="Enclave session handle")
    computation_type: str = Field(..., description="Computation executed")
    status: str = Field(..., description="Enclave computation status")
    party_a_record_count: int = Field(..., description="Hospital A record count")
    party_b_record_count: int = Field(..., description="Hospital B record count")
    shared_patients_identified: int = Field(..., description="Cohort intersection size")
    joint_cohort_metrics: Dict[str, Any] = Field(..., description="In-enclave computed statistics")
    confidentiality_guarantee: str = Field(..., description="Cryptographic confidentiality guarantee")
    hardware_execution_seal: str = Field(..., description="Silicon execution proof token")
    timestamp_iso: str = Field(..., description="Completion timestamp")


# ---------------------------------------------------------------------------
# 3. Autonomous Adaptive Join Optimizer Schemas
# ---------------------------------------------------------------------------

class AdaptiveJoinOptimizeRequest(BaseModel):
    table_a: List[Dict[str, Any]] = Field(..., description="Left relation records")
    table_b: List[Dict[str, Any]] = Field(..., description="Right relation records")
    join_key: str = Field(..., description="Equi-join key column name")


class AdaptiveJoinOptimizeResponse(BaseModel):
    strategy: str = Field(..., description="Chosen physical join strategy")
    table_a_cardinality: int = Field(..., description="Left relation row count")
    table_b_cardinality: int = Field(..., description="Right relation row count")
    table_a_distinct_keys: int = Field(..., description="HyperLogLog estimated distinct keys in Table A")
    table_b_distinct_keys: int = Field(..., description="HyperLogLog estimated distinct keys in Table B")
    skew_ratio: float = Field(..., description="Count-Min sketch detected maximum key frequency ratio")
    estimated_memory_kb: float = Field(..., description="Estimated memory footprint in KB")
    rationale: str = Field(..., description="Physical operator selection rationale")
    output_rows: int = Field(..., description="Resulting join rows")
    execution_time_microseconds: float = Field(..., description="Execution duration in microseconds")
    joined_records: List[Dict[str, Any]] = Field(..., description="Joined output records")
