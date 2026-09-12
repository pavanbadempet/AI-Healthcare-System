"""
FastAPI Router for Peak Healthcare Data Engineering:
- Bi-Temporal Event Sourcing & Point-in-Time (PIT) As-Of Joins
- Zero-Copy Streaming Kappa Architecture with Apache Arrow
- Enforceable Enterprise Data Contracts & Schema Drift DLQ
- (epsilon, delta)-Differential Privacy Synthetic EHR Cohorts
- Point-in-Time Feature Store with Automated Drift Monitoring (PSI, Wasserstein)
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from backend.data_platform.bitemporal_engine import bitemporal_engine
from backend.data_platform.data_contracts import contract_enforcement_engine
from backend.data_platform.differential_privacy_engine import dp_synth_engine
from backend.data_platform.feature_drift_monitor import feature_drift_monitor
from backend.data_platform.kappa_streaming import kappa_streaming_engine
from backend.schemas.peak_data_engineering import (
    BiTemporalAmendRequest,
    BiTemporalAsOfQueryRequest,
    BiTemporalAsOfQueryResponse,
    BiTemporalInsertRequest,
    BiTemporalRecordResponse,
    ContractValidationRequest,
    ContractValidationResponse,
    DifferentialPrivacySynthesisRequest,
    DifferentialPrivacySynthesisResponse,
    FeatureDriftAuditRequest,
    FeatureDriftAuditResponse,
    StreamingBatchIngestRequest,
    StreamingBatchIngestResponse,
    StreamingWindowAggregateRequest,
    StreamingWindowAggregateResponse,
)

logger = logging.getLogger("backend.data_engineering_routes")

router = APIRouter(prefix="/v1/data-engineering", tags=["Peak Healthcare Data Engineering"])


# --- Bi-Temporal Endpoints ---
@router.post(
    "/bitemporal/insert",
    response_model=BiTemporalRecordResponse,
    summary="Insert Bi-Temporal Clinical Observation",
)
def insert_bitemporal_record(request: BiTemporalInsertRequest) -> BiTemporalRecordResponse:
    """
    Inserts a record with dual time clocks: valid_time (occurrence) and system_time (ingestion).
    """
    try:
        vt = datetime.fromisoformat(request.valid_time_iso.replace("Z", "+00:00"))
        st = datetime.fromisoformat(request.system_time_iso.replace("Z", "+00:00")) if request.system_time_iso else None
        rec = bitemporal_engine.insert_clinical_event(
            record_id=request.record_id,
            entity_id=request.entity_id,
            attribute_name=request.attribute_name,
            attribute_value=request.attribute_value,
            valid_time=vt,
            unit=request.unit,
            system_time=st,
        )
        return BiTemporalRecordResponse(
            record_id=rec.record_id,
            entity_id=rec.entity_id,
            attribute_name=rec.attribute_name,
            attribute_value=rec.attribute_value,
            unit=rec.unit,
            valid_time_start=rec.valid_time_start.isoformat(),
            valid_time_end=rec.valid_time_end.isoformat(),
            system_time_start=rec.system_time_start.isoformat(),
            system_time_end=rec.system_time_end.isoformat(),
            version=rec.version,
        )
    except Exception as e:
        logger.error(f"Bi-temporal insert failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to insert bi-temporal clinical record",
        )


@router.post(
    "/bitemporal/amend",
    response_model=BiTemporalRecordResponse,
    summary="Retroactively Amend Past Clinical Record",
)
def amend_bitemporal_record(request: BiTemporalAmendRequest) -> BiTemporalRecordResponse:
    """
    Retroactively amends a past record. The old record is closed in system-time;
    the new amended record is inserted with incremented version. History remains immutable.
    """
    try:
        vt = datetime.fromisoformat(request.effective_valid_time_iso.replace("Z", "+00:00"))
        _, new_rec = bitemporal_engine.amend_clinical_event(
            entity_id=request.entity_id,
            attribute_name=request.attribute_name,
            new_attribute_value=request.new_attribute_value,
            effective_valid_time=vt,
            amendment_reason=request.amendment_reason,
            amended_by=request.amended_by,
        )
        return BiTemporalRecordResponse(
            record_id=new_rec.record_id,
            entity_id=new_rec.entity_id,
            attribute_name=new_rec.attribute_name,
            attribute_value=new_rec.attribute_value,
            unit=new_rec.unit,
            valid_time_start=new_rec.valid_time_start.isoformat(),
            valid_time_end=new_rec.valid_time_end.isoformat(),
            system_time_start=new_rec.system_time_start.isoformat(),
            system_time_end=new_rec.system_time_end.isoformat(),
            version=new_rec.version,
        )
    except Exception as e:
        logger.error(f"Bi-temporal amendment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to amend bi-temporal record",
        )


@router.post(
    "/bitemporal/as-of-query",
    response_model=BiTemporalAsOfQueryResponse,
    summary="Point-in-Time As-Of Feature Query (Zero Leakage)",
)
def query_bitemporal_as_of(request: BiTemporalAsOfQueryRequest) -> BiTemporalAsOfQueryResponse:
    """
    Executes a Point-in-Time state reconstruction: queries what the system knew at system_time
    regarding the patient at valid_time.
    """
    try:
        vt = datetime.fromisoformat(request.as_of_valid_time_iso.replace("Z", "+00:00"))
        st = datetime.fromisoformat(request.as_of_system_time_iso.replace("Z", "+00:00"))
        res = bitemporal_engine.query_as_of(
            entity_id=request.entity_id,
            valid_time=vt,
            system_time=st,
        )
        return BiTemporalAsOfQueryResponse(
            entity_id=res.entity_id,
            as_of_valid_time=res.as_of_valid_time.isoformat(),
            as_of_system_time=res.as_of_system_time.isoformat(),
            features=res.features,
            active_versions=res.active_versions,
            zero_leakage_verified=res.zero_leakage_verified,
        )
    except Exception as e:
        logger.error(f"Bi-temporal query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute point-in-time bi-temporal query",
        )


# --- Streaming Kappa Endpoints ---
@router.post(
    "/streaming/ingest-batch",
    response_model=StreamingBatchIngestResponse,
    summary="Zero-Copy Ingest Telemetry Batch via Apache Arrow",
)
def ingest_streaming_batch(request: StreamingBatchIngestRequest) -> StreamingBatchIngestResponse:
    """
    Ingests streaming bedside vitals directly into zero-copy Apache Arrow in-memory columnar buffers.
    """
    try:
        dicts = [rec.model_dump() for rec in request.records]
        batch = kappa_streaming_engine.ingest_batch_arrow(dicts, table_name=request.table_name)
        return StreamingBatchIngestResponse(
            ingested_count=len(dicts),
            table_name=request.table_name,
            arrow_num_columns=batch.num_columns,
            zero_copy_success=True,
        )
    except Exception as e:
        logger.error(f"Streaming batch ingest failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest streaming telemetry batch",
        )


@router.post(
    "/streaming/window-aggregates",
    response_model=StreamingWindowAggregateResponse,
    summary="Compute Sliding/Tumbling Window Columnar Aggregates",
)
def compute_streaming_window(request: StreamingWindowAggregateRequest) -> StreamingWindowAggregateResponse:
    """
    Computes zero-copy columnar aggregations (mean, std, min, max, slope) over a streaming temporal window.
    """
    try:
        agg = kappa_streaming_engine.compute_windowed_aggregates(
            patient_id=request.patient_id,
            metric_name=request.metric_name,
            window_duration_seconds=request.window_duration_seconds,
            window_type=request.window_type,
        )
        if agg is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No telemetry observations found for patient '{request.patient_id}' and metric '{request.metric_name}' in window.",
            )
        return StreamingWindowAggregateResponse(
            patient_id=agg.patient_id,
            metric_name=agg.metric_name,
            window_type=agg.window_type,
            window_duration_seconds=agg.window_duration_seconds,
            window_end_epoch_ms=agg.window_end_epoch_ms,
            count=agg.count,
            mean=agg.mean,
            std_dev=agg.std_dev,
            min_val=agg.min_val,
            max_val=agg.max_val,
            slope_velocity=agg.slope_velocity,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Window aggregate failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute streaming window aggregates",
        )


# --- Enterprise Data Contracts Endpoints ---
@router.post(
    "/contracts/validate",
    response_model=ContractValidationResponse,
    summary="Validate Payload Against Perimeter Data Contract",
)
def validate_contract_payload(request: ContractValidationRequest) -> ContractValidationResponse:
    """
    Validates payload against registered Data Contract. Non-compliant records are diverted to DLQ.
    """
    try:
        res = contract_enforcement_engine.validate_payload(
            contract_id=request.contract_id,
            payload=request.payload,
        )
        return ContractValidationResponse(
            is_valid=res.is_valid,
            contract_id=res.contract_id,
            dataset_name=res.dataset_name,
            passed_fields=res.passed_fields,
            violations=[
                {
                    "field_name": v.field_name,
                    "violation_type": v.violation_type,
                    "expected": v.expected,
                    "actual": v.actual,
                    "severity": v.severity,
                }
                for v in res.violations
            ],
            quarantined=res.quarantined,
            quarantine_id=res.quarantine_id,
            drift_detected=res.drift_detected,
            new_uncontracted_fields=res.new_uncontracted_fields,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Contract validation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute contract validation",
        )


# --- Differential Privacy Synthetic EHR ---
@router.post(
    "/privacy/synthesize-cohort",
    response_model=DifferentialPrivacySynthesisResponse,
    summary="Generate (epsilon, delta)-Differentially Private Synthetic Cohort",
)
def synthesize_dp_cohort(request: DifferentialPrivacySynthesisRequest) -> DifferentialPrivacySynthesisResponse:
    """
    Generates high-fidelity synthetic patient cohorts with mathematically certified zero-re-identification guarantees.
    """
    try:
        res = dp_synth_engine.synthesize_cohort(
            cohort_id=request.cohort_id,
            n_patients=request.n_patients,
            epsilon=request.epsilon,
            delta=request.delta,
        )
        return DifferentialPrivacySynthesisResponse(
            cohort_id=res.cohort_id,
            num_synthesized=res.num_synthesized,
            epsilon_used=res.epsilon_used,
            delta_used=res.delta_used,
            privacy_mechanism=res.privacy_mechanism,
            empirical_covariance_preserved=res.empirical_covariance_preserved,
            synthetic_records=[
                {
                    "synthetic_patient_id": r.synthetic_patient_id,
                    "age": r.age,
                    "gender": r.gender,
                    "systolic_bp": r.systolic_bp,
                    "diastolic_bp": r.diastolic_bp,
                    "serum_creatinine": r.serum_creatinine,
                    "egfr": r.egfr,
                    "hba1c": r.hba1c,
                    "blood_glucose": r.blood_glucose,
                    "primary_icd10": r.primary_icd10,
                    "mace_risk_percent": r.mace_risk_percent,
                }
                for r in res.synthetic_records
            ],
            privacy_budget_status={
                "epsilon_budget": res.privacy_budget_status.epsilon_budget,
                "delta_budget": res.privacy_budget_status.delta_budget,
                "epsilon_spent": res.privacy_budget_status.epsilon_spent,
                "delta_spent": res.privacy_budget_status.delta_spent,
                "remaining_epsilon": res.privacy_budget_status.remaining_epsilon,
                "budget_exhausted": res.privacy_budget_status.budget_exhausted,
            },
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"DP synthesis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synthesize differentially private cohort",
        )


# --- Feature Store & Drift Monitoring ---
@router.post(
    "/features/drift-audit",
    response_model=FeatureDriftAuditResponse,
    summary="Audit Feature Covariate Drift (PSI, Wasserstein, KS-Test)",
)
def audit_feature_drift(request: FeatureDriftAuditRequest) -> FeatureDriftAuditResponse:
    """
    Evaluates real-time Population Stability Index (PSI) and Wasserstein distance for clinical features.
    """
    try:
        report = feature_drift_monitor.audit_feature_drift(
            feature_name=request.feature_name,
            current_samples=request.current_samples,
        )
        return FeatureDriftAuditResponse(
            feature_name=report.feature_name,
            sample_size_baseline=report.sample_size_baseline,
            sample_size_current=report.sample_size_current,
            psi_score=report.psi_score,
            wasserstein_distance_score=report.wasserstein_distance_score,
            ks_statistic=report.ks_statistic,
            ks_p_value=report.ks_p_value,
            drift_status=report.drift_status,
            requires_retraining=report.requires_retraining,
            recommended_action=report.recommended_action,
            bucket_distributions=report.bucket_distributions,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Feature drift audit failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to audit feature drift",
        )
