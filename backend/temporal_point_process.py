"""
Marked Temporal Point Process (TPP) & Multivariate Hawkes Process Engine.

Models the exact arrival times, triggering dynamics, and cascading frequencies
of acute clinical events (acute decompensation, ICU shock alerts, hypoglycemic crashes,
malignant arrhythmias, readmission cycles) across time.

Implements:
1. Multivariate Hawkes Process with exponential decay kernels:
   lambda_m(t | H_t) = mu_m + sum_{j=1}^M sum_{t_{j,k} < t} alpha_{mj} * exp(-beta_{mj} * (t - t_{j,k}))
2. Spectral radius verification rho(Gamma) < 1 for branching stationarity.
3. Ogata's modified thinning simulation algorithm for event forecasting.
4. Instantaneous intensity estimation and conditional next-event hazard density.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

logger = logging.getLogger("backend.temporal_point_process")


@dataclass
class ClinicalHistoricalEvent:
    timestamp_hours: float  # hours relative to baseline t=0
    event_type: str  # e.g. "ACUTE_DECOMPENSATION", "SEPSIS_ALERT", "HYPOGLYCEMIC_SHOCK", "ARRHYTHMIA"
    severity_mark: float = 1.0  # continuous mark / magnitude multiplier


@dataclass
class ProjectedEventArrival:
    simulated_arrival_hour: float
    hours_from_now: float
    predicted_event_type: str
    probability_confidence: float


@dataclass
class TemporalPointProcessForecast:
    patient_id: str
    current_time_hours: float
    instantaneous_intensities: Dict[str, float]  # lambda_m(t) events per hour
    dominant_near_term_threat: str
    expected_time_to_next_event_hours: float
    horizon_event_probabilities: Dict[str, float]  # e.g. {"24_hour": 0.42, "72_hour": 0.78, "7_day": 0.93}
    branching_ratio_spectral_radius: float
    system_is_subcritical: bool  # True if rho(Gamma) < 1 (non-explosive)
    simulated_next_arrivals: List[ProjectedEventArrival]


class TemporalPointProcessEngine:
    """
    Multivariate Hawkes Process Engine for High-Frequency Clinical Cascade Forecasting.
    """

    def __init__(self) -> None:
        self._event_types = [
            "ACUTE_DECOMPENSATION",
            "SEPSIS_ALERT",
            "HYPOGLYCEMIC_SHOCK",
            "ARRHYTHMIA",
            "LAB_PANIC_VALUE",
        ]
        self._event_to_idx = {name: i for i, name in enumerate(self._event_types)}
        self._M = len(self._event_types)

        # Baseline intensities (events per hour in an unexcited state)
        self._mu = np.array([0.005, 0.003, 0.004, 0.002, 0.010])

        # Cross-excitation matrix Alpha (alpha_mj: event j triggers event m)
        # Scaled so the spectral radius of Gamma = Alpha / Beta is strictly < 1.0 (subcritical)
        raw_alpha = np.array([
            [0.25, 0.35, 0.10, 0.20, 0.15],  # DECOMPENSATION triggered by sepsis/arrhythmia
            [0.10, 0.30, 0.05, 0.05, 0.20],  # SEPSIS triggered by lab panics/sepsis
            [0.05, 0.05, 0.25, 0.02, 0.10],  # HYPOGLYCEMIA triggered by prior hypogly
            [0.30, 0.20, 0.15, 0.35, 0.10],  # ARRHYTHMIA triggered by decomp/hypo/arrhythmia
            [0.20, 0.40, 0.15, 0.10, 0.25],  # LAB_PANIC triggered by sepsis/decomp
        ])

        # Decay rates Beta (half-life of excitation in hours^-1)
        # beta=0.5 -> half-life ~ 1.38 hours
        self._beta = np.full((self._M, self._M), 0.50)

        # Scale raw_alpha such that spectral radius rho(Gamma) = 0.72 (subcritical)
        raw_gamma = raw_alpha / self._beta
        raw_spec_radius = float(np.max(np.abs(np.linalg.eigvals(raw_gamma))))
        scale_factor = 0.72 / max(raw_spec_radius, 1e-6)

        self._alpha = raw_alpha * scale_factor
        self._gamma = self._alpha / self._beta
        eigenvalues = np.linalg.eigvals(self._gamma)
        self._spectral_radius = float(np.max(np.abs(eigenvalues)))

    def calculate_intensities(
        self,
        current_time_hours: float,
        history: List[ClinicalHistoricalEvent],
    ) -> np.ndarray:
        """
        Computes current instantaneous intensity vector lambda(t | H_t) for all event types.
        lambda_m(t) = mu_m + sum_{t_k < t} alpha_{m, j_k} * mark_k * exp(-beta_{m, j_k} * (t - t_k))
        """
        intensities = self._mu.copy()

        for ev in history:
            if ev.timestamp_hours >= current_time_hours:
                continue
            delta_t = current_time_hours - ev.timestamp_hours
            if delta_t < 0:
                continue

            j_idx = self._event_to_idx.get(ev.event_type)
            if j_idx is None:
                continue

            mark = max(0.5, ev.severity_mark)
            for m_idx in range(self._M):
                decay = math.exp(-self._beta[m_idx, j_idx] * delta_t)
                intensities[m_idx] += self._alpha[m_idx, j_idx] * mark * decay

        return intensities

    def simulate_ogata_thinning(
        self,
        current_time_hours: float,
        history: List[ClinicalHistoricalEvent],
        horizon_hours: float = 72.0,
        max_events: int = 5,
    ) -> List[ProjectedEventArrival]:
        """
        Simulates forward trajectories of future arrival times using Ogata's thinning algorithm.
        """
        sim_history = list(history)
        t = current_time_hours
        t_end = current_time_hours + horizon_hours
        simulated: List[ProjectedEventArrival] = []

        rng = np.random.RandomState(42)

        while t < t_end and len(simulated) < max_events:
            current_lambdas = self.calculate_intensities(t, sim_history)
            lambda_bar = float(np.sum(current_lambdas))
            if lambda_bar <= 1e-6:
                break

            # Draw candidate time step from homogeneous Poisson process with rate lambda_bar
            u1 = rng.uniform(1e-7, 1.0)
            delta_t = -math.log(u1) / lambda_bar
            t_cand = t + delta_t
            if t_cand > t_end:
                break

            # Re-evaluate intensity at candidate time
            lambdas_at_cand = self.calculate_intensities(t_cand, sim_history)
            lambda_cand = float(np.sum(lambdas_at_cand))

            # Acceptance-rejection thinning step
            u2 = rng.uniform(0.0, 1.0)
            if u2 <= (lambda_cand / lambda_bar):
                # Candidate accepted! Attribute event type proportionally to lambdas
                probs = lambdas_at_cand / lambda_cand
                chosen_idx = int(rng.choice(self._M, p=probs))
                ev_name = self._event_types[chosen_idx]

                new_event = ClinicalHistoricalEvent(
                    timestamp_hours=t_cand,
                    event_type=ev_name,
                    severity_mark=1.0,
                )
                sim_history.append(new_event)
                t = t_cand

                simulated.append(
                    ProjectedEventArrival(
                        simulated_arrival_hour=round(t_cand, 2),
                        hours_from_now=round(t_cand - current_time_hours, 2),
                        predicted_event_type=ev_name,
                        probability_confidence=round(float(probs[chosen_idx]), 3),
                    )
                )
            else:
                # Rejected; advance time to t_cand and continue
                t = t_cand

        return simulated

    def forecast_cascade(
        self,
        patient_id: str,
        current_time_hours: float,
        history: List[ClinicalHistoricalEvent],
    ) -> TemporalPointProcessForecast:
        """
        Generates full temporal point process forecasting report for an individual patient.
        """
        intensities = self.calculate_intensities(current_time_hours, history)
        intensity_dict = {
            name: round(float(intensities[i]), 5)
            for i, name in enumerate(self._event_types)
        }

        # Dominant near-term threat (highest intensity)
        dominant_idx = int(np.argmax(intensities))
        dominant_threat = self._event_types[dominant_idx]

        total_intensity = float(np.sum(intensities))
        # Expected time to next event (approx 1 / total_lambda in hours)
        if total_intensity > 1e-6:
            expected_delta = round(1.0 / total_intensity, 2)
        else:
            expected_delta = 999.0

        # Cumulative probability of at least one event in 24h, 72h, 7d (168h)
        # P(T <= delta) = 1 - exp(-int lambda(s) ds) ~ 1 - exp(-total_lambda * delta)
        prob_24h = round(float(1.0 - math.exp(-min(total_intensity * 24.0, 15.0))), 4)
        prob_72h = round(float(1.0 - math.exp(-min(total_intensity * 72.0, 15.0))), 4)
        prob_7d = round(float(1.0 - math.exp(-min(total_intensity * 168.0, 15.0))), 4)

        simulated_arrivals = self.simulate_ogata_thinning(
            current_time_hours=current_time_hours,
            history=history,
            horizon_hours=168.0,
            max_events=5,
        )

        return TemporalPointProcessForecast(
            patient_id=patient_id,
            current_time_hours=round(current_time_hours, 2),
            instantaneous_intensities=intensity_dict,
            dominant_near_term_threat=dominant_threat,
            expected_time_to_next_event_hours=expected_delta,
            horizon_event_probabilities={
                "24_hour": prob_24h,
                "72_hour": prob_72h,
                "7_day": prob_7d,
            },
            branching_ratio_spectral_radius=round(self._spectral_radius, 4),
            system_is_subcritical=(self._spectral_radius < 1.0),
            simulated_next_arrivals=simulated_arrivals,
        )


tpp_engine = TemporalPointProcessEngine()
