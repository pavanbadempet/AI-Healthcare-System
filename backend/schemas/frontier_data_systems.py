"""
Pydantic Schemas for Level 6 Frontier Data Systems & Cryptographic Engines.

Enforces strict input/output contract validation for:
- Zero-Knowledge ETL Provenance (zk-ETL)
- Secure Multi-Party Computation & Private Set Intersection (SMPC & PSI)
- SIMD Vectorized Columnar Execution Engine
- Autonomous Storage Graph & Z-Order Space-Filling Partitioner
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Zero-Knowledge ETL Provenance Schemas
# ---------------------------------------------------------------------------

class ZkEtlProveRequest(BaseModel):
    transformation_name: str = Field(..., description="Canonical name of deterministic transformation")
    pipeline_stage: str = Field(default="BRONZE_TO_SILVER", description="Data pipeline transition stage")
    input_records: List[Dict[str, Any]] = Field(..., description="Upstream input records")
    output_records: List[Dict[str, Any]] = Field(..., description="Downstream transformed output records")


class ZkEtlProofResponse(BaseModel):
    proof_token: str = Field(..., description="Unique cryptographic proof token")
    transformation_name: str = Field(..., description="Transformation identifier")
    input_merkle_root: str = Field(..., description="SHA-256 Merkle root of input records")
    output_merkle_root: str = Field(..., description="SHA-256 Merkle root of output records")
    num_input_records: int = Field(..., description="Input row count")
    num_output_records: int = Field(..., description="Output row count")
    pipeline_stage: str = Field(..., description="Pipeline execution stage")
    timestamp_iso: str = Field(..., description="Proof generation timestamp")
    execution_digest: str = Field(..., description="Cryptographic execution digest")
    mathematically_verified: bool = Field(default=True, description="Self-verification status")


class ZkEtlVerifyRequest(BaseModel):
    proof_token: str = Field(..., description="Proof token to audit")
    claimed_input_records: List[Dict[str, Any]] = Field(..., description="Claimed source records")
    claimed_output_records: List[Dict[str, Any]] = Field(..., description="Claimed target records")


class ZkEtlVerifyResponse(BaseModel):
    verified: bool = Field(..., description="Whether cryptographic provenance holds")
    details: str = Field(..., description="Verification verdict and explanation")
    proof_token: str = Field(..., description="Audited token")


# ---------------------------------------------------------------------------
# 2. SMPC & Private Set Intersection (PSI) Schemas
# ---------------------------------------------------------------------------

class SmpcPsiRequest(BaseModel):
    identifiers_a: List[str] = Field(..., description="Cohort patient tokens from Institution A")
    identifiers_b: List[str] = Field(..., description="Cohort patient tokens from Institution B")
    institution_a_id: str = Field(default="HOSPITAL_ALPHA", description="Institution A identifier")
    institution_b_id: str = Field(default="HOSPITAL_BETA", description="Institution B identifier")


class SmpcPsiResponse(BaseModel):
    intersection_size: int = Field(..., description="Number of patients in shared intersection")
    matched_double_blinded_tokens: List[str] = Field(..., description="Double-blinded matched tokens")
    cohort_alpha_size: int = Field(..., description="Total size of Cohort A")
    cohort_beta_size: int = Field(..., description="Total size of Cohort B")
    jaccard_similarity: float = Field(..., description="Jaccard overlap coefficient")
    cryptographic_scheme: str = Field(default="Commutative-DH-P256-PSI", description="Cryptographic protocol")


class SmpcSecretShareRequest(BaseModel):
    values_a: List[float] = Field(..., description="Clinical metric values from Party A (e.g. eGFR)")
    values_b: List[float] = Field(..., description="Clinical metric values from Party B (e.g. eGFR)")
    scale_factor: int = Field(default=1000, description="Fixed-point scaling factor")


class SmpcSecretShareResponse(BaseModel):
    protocol: str = Field(default="2-Party-Additive-Secret-Sharing", description="Protocol name")
    total_records: int = Field(..., description="Combined patient count")
    party_a_count: int = Field(..., description="Party A count")
    party_b_count: int = Field(..., description="Party B count")
    federated_sum: float = Field(..., description="Cryptographically computed federated sum")
    federated_mean: float = Field(..., description="Cryptographically computed federated mean")
    zero_leakage_guarantee: bool = Field(default=True, description="Mathematical zero disclosure guarantee")


# ---------------------------------------------------------------------------
# 3. SIMD Vector Execution Engine Schemas
# ---------------------------------------------------------------------------

class PredicateDefinition(BaseModel):
    column: str = Field(..., description="Column to filter")
    operator: str = Field(..., description="Filter operator (==, !=, >, >=, <, <=, in, between)")
    value: Any = Field(..., description="Predicate operand value or range")


class SimdExecutionMetricsSchema(BaseModel):
    total_records_scanned: int = Field(..., description="Input records scanned")
    matched_records: int = Field(..., description="Records satisfying predicates")
    selectivity_pct: float = Field(..., description="Predicate selectivity percentage")
    filter_latency_microseconds: float = Field(..., description="Filter scan latency in microseconds")
    aggregate_latency_microseconds: float = Field(..., description="Aggregation latency in microseconds")
    total_latency_microseconds: float = Field(..., description="Total execution latency in microseconds")
    throughput_records_per_sec: float = Field(..., description="Vector execution throughput")


class SimdVectorQueryRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="Input columnar records")
    predicates: List[PredicateDefinition] = Field(default_factory=list, description="Vector filter predicates")
    aggregate_columns: List[str] = Field(default_factory=list, description="Columns to aggregate")


class SimdVectorQueryResponse(BaseModel):
    filtered_records: List[Dict[str, Any]] = Field(..., description="Filtered dataset rows")
    aggregates: Dict[str, Dict[str, Any]] = Field(..., description="Columnar summary statistics")
    metrics: SimdExecutionMetricsSchema = Field(..., description="Execution speed and throughput metrics")


# ---------------------------------------------------------------------------
# 4. Autonomous Storage Graph & Z-Order Schemas
# ---------------------------------------------------------------------------

class StorageQueryLogRequest(BaseModel):
    query_id: str = Field(..., description="Unique query identifier")
    columns_referenced: List[str] = Field(..., description="Columns accessed in projection or filters")
    filter_predicates: Dict[str, Any] = Field(default_factory=dict, description="Predicate terms")
    rows_scanned: int = Field(..., description="Rows scanned from physical storage")
    rows_returned: int = Field(..., description="Rows returned after filtering")
    execution_time_ms: float = Field(..., description="Query run latency in milliseconds")


class StorageAffinityGraphResponse(BaseModel):
    total_queries_analyzed: int = Field(..., description="Workload queries tracked")
    columns_tracked: int = Field(..., description="Distinct columns observed")
    nodes: List[Dict[str, Any]] = Field(..., description="Column nodes with access frequencies")
    edges: List[Dict[str, Any]] = Field(..., description="Co-occurrence edge weights")


class StorageZOrderOptimizeRequest(BaseModel):
    num_records: int = Field(default=100_000, description="Hypothetical dataset row count")
    block_size: int = Field(default=1_000, description="Records per storage block/extent")
    dimension_columns: Optional[List[str]] = Field(default=None, description="Explicit clustering dimensions")
    selectivity_per_dim: float = Field(default=0.25, description="Filter selectivity per dimension")


class StorageZOrderOptimizeResponse(BaseModel):
    recommended_clustering_dimensions: List[str] = Field(..., description="Optimal dimensions for Z-ordering")
    co_occurrence_score: float = Field(..., description="Access affinity score")
    estimated_io_pruning_pct: float = Field(..., description="Storage byte-scan reduction percentage")
    simulated_blocks_total: int = Field(..., description="Total blocks in physical storage")
    simulated_blocks_scanned: int = Field(..., description="Blocks touched after Morton pruning")
    morton_bit_depth: int = Field(..., description="Morton curve bit resolution")
    rationale: str = Field(..., description="Physical layout optimization explanation")
