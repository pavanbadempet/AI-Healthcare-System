"""
FastAPI Router for Advanced Clinical Intelligence Systems:
- Conformal Prediction (Finite-sample uncertainty intervals & adaptive diagnostic sets)
- Clinical Survival Analysis (Kaplan-Meier, Cox Proportional Hazards, Competing Risks)
- Polypharmacy Graph Interaction Network (Multi-relational DDI & high-order synergy reasoning)
- Marked Temporal Point Process (Multivariate Hawkes process event arrival cascades)
- Safe Offline Reinforcement Learning (Batch-Constrained DTR policy optimization)
- Topological Data Analysis (Vietoris-Rips persistent homology & Betti manifold profiles)
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.conformal_prediction import conformal_engine
from backend.polypharmacy_graph import polypharmacy_engine
from backend.rl_treatment_optimizer import ClinicalStateObservation, rl_optimizer
from backend.schemas.advanced_intelligence import (
    ConformalClassificationRequest,
    ConformalClassificationResponse,
    ConformalIntervalRequest,
    ConformalIntervalResponse,
    PatientSurvivalRequest,
    PatientSurvivalResponse,
    PolypharmacyEvaluationRequest,
    PolypharmacyEvaluationResponse,
    RlOptimizationRequest,
    RlOptimizationResponse,
    TemporalForecastRequest,
    TemporalForecastResponse,
    TopologicalAnalysisRequest,
    TopologicalAnalysisResponse,
)
from backend.survival_engine import survival_engine
from backend.temporal_point_process import ClinicalHistoricalEvent, tpp_engine
from backend.topological_phenotyping import topological_engine

logger = logging.getLogger("backend.advanced_intelligence_routes")

router = APIRouter(prefix="/v1/advanced", tags=["Advanced Clinical Intelligence"])


@router.post(
    "/conformal-predict-interval",
    response_model=ConformalIntervalResponse,
    summary="Compute Calibrated Conformal Prediction Interval",
)
def compute_conformal_interval(request: ConformalIntervalRequest) -> ConformalIntervalResponse:
    """
    Computes a distribution-free, finite-sample calibrated prediction interval with
    guaranteed coverage P(Y in C(X)) >= 1 - alpha.
    """
    try:
        res = conformal_engine.predict_interval(
            target_name=request.target_name,
            point_estimate=request.point_estimate,
            confidence_level=request.confidence_level,
            local_spread_factor=request.local_spread_factor,
            custom_calibration_residuals=request.custom_calibration_residuals,
        )
        return ConformalIntervalResponse(
            target_name=res.target_name,
            point_estimate=res.point_estimate,
            lower_bound=res.lower_bound,
            upper_bound=res.upper_bound,
            confidence_level=res.confidence_level,
            interval_width=res.interval_width,
            method=res.method,
            finite_sample_guaranteed=res.finite_sample_guaranteed,
        )
    except Exception as e:
        logger.error(f"Conformal interval generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate conformal prediction interval",
        )


@router.post(
    "/conformal-predict-set",
    response_model=ConformalClassificationResponse,
    summary="Compute Adaptive Conformal Prediction Set",
)
def compute_conformal_set(request: ConformalClassificationRequest) -> ConformalClassificationResponse:
    """
    Computes an Adaptive Prediction Set (APS) for multi-class differential diagnosis
    with guaranteed true-class inclusion probability >= 1 - alpha.
    """
    try:
        res = conformal_engine.predict_classification_set(
            candidate_probabilities=request.candidate_probabilities,
            confidence_level=request.confidence_level,
        )
        return ConformalClassificationResponse(
            diagnostic_category=res.diagnostic_category,
            prediction_set=res.prediction_set,
            confidence_level=res.confidence_level,
            set_cardinality=res.set_cardinality,
            class_probabilities=res.class_probabilities,
            ambiguity_flag=res.ambiguity_flag,
        )
    except Exception as e:
        logger.error(f"Conformal prediction set generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate adaptive prediction set",
        )


@router.post(
    "/survival-analysis",
    response_model=PatientSurvivalResponse,
    summary="Project Time-to-Event Survival Curve & Competing Risks",
)
def project_survival_analysis(request: PatientSurvivalRequest) -> PatientSurvivalResponse:
    """
    Computes patient-specific survival curve, median survival time, 1/3/5-year survival probabilities,
    and cause-specific competing risk cumulative incidences.
    """
    try:
        res = survival_engine.predict_patient_survival(
            patient_id=request.patient_id,
            condition=request.condition,
            age=request.age,
            biomarkers=request.biomarkers,
            active_therapies=request.active_therapies,
        )
        return PatientSurvivalResponse(
            patient_id=res.patient_id,
            condition=res.condition,
            median_survival_months=res.median_survival_months,
            survival_probabilities=res.survival_probabilities,
            competing_risk_probabilities=res.competing_risk_probabilities,
            individual_hazard_ratio=res.individual_hazard_ratio,
            risk_tier=res.risk_tier,
            survival_curve=[
                {
                    "time_months": pt.time_months,
                    "survival_probability": pt.survival_probability,
                    "lower_ci": pt.lower_ci,
                    "upper_ci": pt.upper_ci,
                    "n_at_risk": pt.n_at_risk,
                    "n_events": pt.n_events,
                }
                for pt in res.survival_curve
            ],
        )
    except Exception as e:
        logger.error(f"Survival analysis projection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute clinical survival projection",
        )


@router.post(
    "/polypharmacy-evaluate",
    response_model=PolypharmacyEvaluationResponse,
    summary="Evaluate Polypharmacy Regimen & High-Order Synergies",
)
def evaluate_polypharmacy(request: PolypharmacyEvaluationRequest) -> PolypharmacyEvaluationResponse:
    """
    Evaluates multi-relational drug-drug interaction graph, detects pairwise risks and
    high-order 3-way syndromes (e.g. Triple Whammy AKI), and recommends safe substitutions.
    """
    try:
        res = polypharmacy_engine.evaluate_regimen(request.drug_list)
        return PolypharmacyEvaluationResponse(
            regimen=res.regimen,
            num_drugs=res.num_drugs,
            regimen_toxicity_index=res.regimen_toxicity_index,
            highest_severity=res.highest_severity,
            pairwise_interactions=[
                {
                    "drug_a": p.drug_a,
                    "drug_b": p.drug_b,
                    "severity": p.severity,
                    "interaction_type": p.interaction_type,
                    "mechanism": p.mechanism,
                    "clinical_risk": p.clinical_risk,
                    "confidence_score": p.confidence_score,
                    "recommended_action": p.recommended_action,
                }
                for p in res.pairwise_interactions
            ],
            high_order_synergies=[
                {
                    "involved_drugs": h.involved_drugs,
                    "synergy_name": h.synergy_name,
                    "synergy_type": h.synergy_type,
                    "severity": h.severity,
                    "mechanism": h.mechanism,
                    "organ_risk": h.organ_risk,
                    "mitigation_strategy": h.mitigation_strategy,
                }
                for h in res.high_order_synergies
            ],
            safer_substitutions=res.safer_substitutions,
            is_contraindicated=res.is_contraindicated,
        )
    except Exception as e:
        logger.error(f"Polypharmacy evaluation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate polypharmacy regimen",
        )


@router.post(
    "/temporal-forecast",
    response_model=TemporalForecastResponse,
    summary="Forecast Clinical Event Cascade via Hawkes Process",
)
def forecast_temporal_cascade(request: TemporalForecastRequest) -> TemporalForecastResponse:
    """
    Forecasts instantaneous event arrival hazard rates, near-term threats, and forward
    simulated trajectories using a Multivariate Hawkes Temporal Point Process.
    """
    try:
        events = [
            ClinicalHistoricalEvent(
                timestamp_hours=ev.timestamp_hours,
                event_type=ev.event_type,
                severity_mark=ev.severity_mark,
            )
            for ev in request.history
        ]
        res = tpp_engine.forecast_cascade(
            patient_id=request.patient_id,
            current_time_hours=request.current_time_hours,
            history=events,
        )
        return TemporalForecastResponse(
            patient_id=res.patient_id,
            current_time_hours=res.current_time_hours,
            instantaneous_intensities=res.instantaneous_intensities,
            dominant_near_term_threat=res.dominant_near_term_threat,
            expected_time_to_next_event_hours=res.expected_time_to_next_event_hours,
            horizon_event_probabilities=res.horizon_event_probabilities,
            branching_ratio_spectral_radius=res.branching_ratio_spectral_radius,
            system_is_subcritical=res.system_is_subcritical,
            simulated_next_arrivals=[
                {
                    "simulated_arrival_hour": arr.simulated_arrival_hour,
                    "hours_from_now": arr.hours_from_now,
                    "predicted_event_type": arr.predicted_event_type,
                    "probability_confidence": arr.probability_confidence,
                }
                for arr in res.simulated_next_arrivals
            ],
        )
    except Exception as e:
        logger.error(f"Temporal cascade forecast failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to forecast temporal event cascade",
        )


@router.post(
    "/rl-optimize-treatment",
    response_model=RlOptimizationResponse,
    summary="Compute Safe Batch-Constrained RL Treatment Policy",
)
def optimize_treatment_policy(request: RlOptimizationRequest) -> RlOptimizationResponse:
    """
    Optimizes sequential clinical dynamic treatment policy using offline batch-constrained
    reinforcement learning with out-of-distribution clinical safety pruning.
    """
    try:
        state_obs = ClinicalStateObservation(
            map_mmhg=request.state.map_mmhg,
            heart_rate_bpm=request.state.heart_rate_bpm,
            lactate_mmol_l=request.state.lactate_mmol_l,
            serum_creatinine=request.state.serum_creatinine,
            urine_output_ml_kg_hr=request.state.urine_output_ml_kg_hr,
            blood_glucose_mg_dl=request.state.blood_glucose_mg_dl,
        )
        res = rl_optimizer.optimize_treatment_policy(
            patient_id=request.patient_id,
            state=state_obs,
            current_vasopressor_dose=request.current_vasopressor_dose,
            current_fluid_rate=request.current_fluid_rate,
            current_insulin_rate=request.current_insulin_rate,
        )
        return RlOptimizationResponse(
            patient_id=res.patient_id,
            recommended_action_id=res.recommended_action_id,
            recommended_action_label=res.recommended_action_label,
            norepinephrine_dose_mcg_kg_min=res.norepinephrine_dose_mcg_kg_min,
            iv_fluid_rate_ml_hr=res.iv_fluid_rate_ml_hr,
            insulin_rate_units_hr=res.insulin_rate_units_hr,
            expected_q_value=res.expected_q_value,
            standard_of_care_q_value=res.standard_of_care_q_value,
            expected_counterfactual_gain=res.expected_counterfactual_gain,
            top_candidate_actions=res.top_candidate_actions,
            clinical_rationale=res.clinical_rationale,
            safety_interlock_cleared=res.safety_interlock_cleared,
        )
    except Exception as e:
        logger.error(f"RL treatment optimization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize clinical treatment policy",
        )


@router.post(
    "/topological-phenotype",
    response_model=TopologicalAnalysisResponse,
    summary="Compute Persistent Homology & Topological Patient Subtypes",
)
def compute_topological_phenotypes(request: TopologicalAnalysisRequest) -> TopologicalAnalysisResponse:
    """
    Computes Vietoris-Rips persistent homology (H0 clusters and H1 cyclical loops),
    Betti curves, and persistent entropy over high-dimensional phenotypic patient manifolds.
    """
    try:
        res = topological_engine.analyze_phenotypic_manifold(
            cohort_id=request.cohort_id,
            patient_feature_matrix=request.patient_feature_matrix,
            feature_names=request.feature_names,
        )
        return TopologicalAnalysisResponse(
            cohort_id=res.cohort_id,
            num_samples=res.num_samples,
            dimension=res.dimension,
            persistent_entropy=res.persistent_entropy,
            num_distinct_subtypes=res.num_distinct_subtypes,
            identified_subtypes=res.identified_subtypes,
            h0_persistence=[
                {
                    "homology_dimension": it.homology_dimension,
                    "birth": it.birth,
                    "death": it.death,
                    "lifetime": it.lifetime,
                    "is_essential": it.is_essential,
                }
                for it in res.h0_persistence
            ],
            h1_persistence=[
                {
                    "homology_dimension": it.homology_dimension,
                    "birth": it.birth,
                    "death": it.death,
                    "lifetime": it.lifetime,
                    "is_essential": it.is_essential,
                }
                for it in res.h1_persistence
            ],
            betti_curves=[
                {
                    "filtration_radius": pt.filtration_radius,
                    "beta_0": pt.beta_0,
                    "beta_1": pt.beta_1,
                }
                for pt in res.betti_curves
            ],
            dominant_topological_feature=res.dominant_topological_feature,
        )
    except Exception as e:
        logger.error(f"Topological phenotyping failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute topological manifold phenotyping",
        )
