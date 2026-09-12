"""
BioTwin-X Cybernetics Engine: Continuous Real-Time Telemetry Data Assimilation.
Implements an Unscented Kalman Filter (UKF) with scaled unscented transformation,
online parameter tracking, and closed-loop hemodynamic instability alerts.
"""

import logging
import math
from typing import List, Tuple

import numpy as np

from backend.schemas.peak_healthcare import (
    CyberneticAssimilationRequest,
    CyberneticAssimilationResponse,
    KalmanStateEstimate,
)

logger = logging.getLogger("backend.clinical_cybernetics")

ORGAN_KEYS = ["cardiovascular", "renal", "metabolic", "hepatic", "neurovascular", "pulmonary"]
NUM_STATES = len(ORGAN_KEYS)  # 6 states
NUM_OBS = 5                   # HR, MAP, SpO2, Blood Glucose, eGFR proxy


class UnscentedKalmanFilter:
    """
    Continuous-Discrete Unscented Kalman Filter (UKF) for nonlinear multi-organ state estimation.
    Applies Julier-Uhlmann scaled unscented transformation across 13 sigma points.
    """

    def __init__(
        self,
        alpha: float = 1e-3,
        beta: float = 2.0,
        kappa_param: float = 0.0,
    ) -> None:
        self.n = NUM_STATES
        self.m = NUM_OBS
        self.alpha = alpha
        self.beta = beta
        self.kappa_param = kappa_param

        # Scaling parameters
        self.lambda_param = (alpha ** 2) * (self.n + kappa_param) - self.n
        self.gamma = math.sqrt(self.n + self.lambda_param)

        # Sigma weights
        self.wm = np.zeros(2 * self.n + 1, dtype=np.float64)
        self.wc = np.zeros(2 * self.n + 1, dtype=np.float64)

        self.wm[0] = self.lambda_param / (self.n + self.lambda_param)
        self.wc[0] = self.wm[0] + (1.0 - alpha ** 2 + beta)

        weight_i = 1.0 / (2.0 * (self.n + self.lambda_param))
        for i in range(1, 2 * self.n + 1):
            self.wm[i] = weight_i
            self.wc[i] = weight_i

        # Process noise covariance (Q) and measurement noise covariance (R)
        self.Q = np.diag([0.05, 0.03, 0.04, 0.02, 0.02, 0.03]).astype(np.float64)
        self.R = np.diag([16.0, 9.0, 2.0, 100.0, 16.0]).astype(np.float64)

    def _generate_sigma_points(self, x: np.ndarray, P: np.ndarray) -> np.ndarray:
        """
        Generates 2n+1 sigma points using Cholesky square root with diagonal jitter.
        """
        sigma_points = np.zeros((2 * self.n + 1, self.n), dtype=np.float64)
        sigma_points[0] = x

        # Ensure positive definiteness with small diagonal jitter
        jitter = np.eye(self.n) * 1e-6
        P_regularized = (P + P.T) / 2.0 + jitter
        try:
            L = np.linalg.cholesky(P_regularized)
        except np.linalg.LinAlgError:
            # Fallback to SVD if Cholesky fails due to conditioning
            u, s, vt = np.linalg.svd(P_regularized)
            L = u @ np.diag(np.sqrt(np.maximum(s, 1e-8)))

        step = self.gamma * L
        for i in range(self.n):
            sigma_points[i + 1] = x + step[:, i]
            sigma_points[self.n + i + 1] = x - step[:, i]

        return np.clip(sigma_points, 1.0, 100.0)

    @staticmethod
    def _state_transition_step(
        x: np.ndarray,
        dt_years: float,
        decay_rates: np.ndarray,
        interventions: List[str],
    ) -> np.ndarray:
        """
        Propagates single state vector through coupled organ differential dynamics over dt_years.
        """
        # Unpack states
        c, r, m, h, n, p = x

        # Cross-organ neuro-humoral coupling
        # Cardiorenal syndrome coupling
        dc_renal = -0.015 * max(0.0, 70.0 - r)
        dr_cardio = -0.018 * max(0.0, 70.0 - c)

        # Glucotoxicity / metabolic resistance
        dm_gluc = -0.02 * max(0.0, 65.0 - m)
        dr_metabolic = -0.012 * max(0.0, 65.0 - m)

        # Hepato-cardiac dyslipidemia
        dh_steatosis = -0.01 * max(0.0, 60.0 - h)

        # Pharmacological/intervention benefit vector
        u_benefit = np.zeros(6, dtype=np.float64)
        interventions_lower = [it.lower() for it in interventions]
        for it in interventions_lower:
            if "sglt2" in it:
                u_benefit[0] += 0.8   # Cardio protection
                u_benefit[1] += 1.4   # Renal preservation
                u_benefit[2] += 0.6   # Glycemic control
            elif "ace" in it or "arb" in it:
                u_benefit[0] += 1.0   # SBP reduction
                u_benefit[1] += 1.2   # Hemodynamic nephroprotection
            elif "glp1" in it or "glp-1" in it:
                u_benefit[0] += 0.7
                u_benefit[2] += 1.8   # Metabolic restoration
                u_benefit[3] += 0.9   # MASH reversal
            elif "statin" in it:
                u_benefit[0] += 1.1
                u_benefit[4] += 0.9   # Stroke/neurovascular

        # Compute continuous derivatives dx/dt
        dx = np.zeros(6, dtype=np.float64)
        dx[0] = -decay_rates[0] * (100.0 - c) + dc_renal + u_benefit[0]
        dx[1] = -decay_rates[1] * (100.0 - r) + dr_cardio + dr_metabolic + u_benefit[1]
        dx[2] = -decay_rates[2] * (100.0 - m) + dm_gluc + u_benefit[2]
        dx[3] = -decay_rates[3] * (100.0 - h) + dh_steatosis + u_benefit[3]
        dx[4] = -decay_rates[4] * (100.0 - n) + 0.3 * dx[0] + u_benefit[4]
        dx[5] = -decay_rates[5] * (100.0 - p) + 0.2 * dx[0] + u_benefit[5]

        # Integrate forward via Euler/Heun integration
        x_next = x + dx * dt_years
        return np.clip(x_next, 1.0, 100.0)

    @staticmethod
    def _observation_model(x: np.ndarray) -> np.ndarray:
        """
        Nonlinear mapping h(x) from 6 hidden organ states to 5 observable vitals:
        y = [HeartRate, MAP, SpO2, BloodGlucose, eGFR_proxy]
        """
        c, r, m, h, n, p = x
        y = np.zeros(NUM_OBS, dtype=np.float64)

        # Heart Rate: resting baseline 68 + sympathetic tone from cardio/pulm decline
        y[0] = 68.0 + 32.0 * ((100.0 - c) / 100.0) + 12.0 * ((100.0 - p) / 100.0)

        # Mean Arterial Pressure: normal 85-95 mmHg + arterial stiffening & cardiorenal resistance
        y[1] = 82.0 + 35.0 * ((100.0 - c) / 100.0) + 18.0 * ((100.0 - r) / 100.0)

        # SpO2 (%): pulmonary gas exchange function
        y[2] = 88.0 + 11.5 * (p / 100.0)

        # Blood Glucose (mg/dL): metabolic insulin sensitivity
        y[3] = 82.0 + 160.0 * ((100.0 - m) / 100.0)

        # eGFR Proxy (mL/min/1.73m^2): glomerular filtration function
        y[4] = 12.0 + 108.0 * (r / 100.0)

        return y

    def filter_step(
        self,
        x_prior: np.ndarray,
        P_prior: np.ndarray,
        y_obs: np.ndarray,
        dt_years: float,
        decay_rates: np.ndarray,
        interventions: List[str],
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, np.ndarray]:
        """
        Executes one full Unscented Kalman Filter assimilation step.

        Returns:
            (x_post, P_post, innovation, innovation_norm, updated_decay_rates)
        """
        num_sigmas = 2 * self.n + 1

        # 1. Generate prior sigma points
        sigmas_prior = self._generate_sigma_points(x_prior, P_prior)

        # 2. Propagate sigma points through nonlinear physiological dynamics
        sigmas_pred = np.zeros_like(sigmas_prior)
        for i in range(num_sigmas):
            sigmas_pred[i] = self._state_transition_step(
                sigmas_prior[i], dt_years, decay_rates, interventions
            )

        # 3. Predicted state mean and covariance
        x_pred = np.zeros(self.n, dtype=np.float64)
        for i in range(num_sigmas):
            x_pred += self.wm[i] * sigmas_pred[i]

        P_pred = np.zeros((self.n, self.n), dtype=np.float64)
        for i in range(num_sigmas):
            diff = (sigmas_pred[i] - x_pred).reshape(-1, 1)
            P_pred += self.wc[i] * (diff @ diff.T)
        P_pred += self.Q * max(0.01, dt_years * 10.0)

        # 4. Predict observations from sigma points
        gamma_obs = np.zeros((num_sigmas, self.m), dtype=np.float64)
        for i in range(num_sigmas):
            gamma_obs[i] = self._observation_model(sigmas_pred[i])

        y_pred = np.zeros(self.m, dtype=np.float64)
        for i in range(num_sigmas):
            y_pred += self.wm[i] * gamma_obs[i]

        # 5. Innovation covariance S and Cross-covariance P_xy
        P_yy = np.zeros((self.m, self.m), dtype=np.float64)
        for i in range(num_sigmas):
            diff_y = (gamma_obs[i] - y_pred).reshape(-1, 1)
            P_yy += self.wc[i] * (diff_y @ diff_y.T)
        P_yy += self.R

        P_xy = np.zeros((self.n, self.m), dtype=np.float64)
        for i in range(num_sigmas):
            diff_x = (sigmas_pred[i] - x_pred).reshape(-1, 1)
            diff_y = (gamma_obs[i] - y_pred).reshape(-1, 1)
            P_xy += self.wc[i] * (diff_x @ diff_y.T)

        # 6. Kalman Gain and Measurement Update
        K = P_xy @ np.linalg.pinv(P_yy)
        innovation = y_obs - y_pred
        innovation_norm = float(np.linalg.norm(innovation))

        x_post = x_pred + (K @ innovation.reshape(-1, 1)).flatten()
        x_post = np.clip(x_post, 1.0, 100.0)

        P_post = P_pred - K @ P_yy @ K.T
        P_post = (P_post + P_post.T) / 2.0  # Ensure symmetry

        # 7. Dynamic parameter adaptation (online parameter tracking)
        # Adapt decay rate according to persistent physiological drift
        updated_decay_rates = decay_rates.copy()
        # If MAP/HR innovation is positive (actual vitals worse than expected), increase cardio decay
        cardio_bias = (innovation[0] / 30.0 + innovation[1] / 30.0) / 2.0
        updated_decay_rates[0] = float(np.clip(decay_rates[0] + 0.05 * cardio_bias * dt_years, 0.005, 0.08))

        # If glucose innovation is positive, increase metabolic decay
        metabolic_bias = innovation[3] / 100.0
        updated_decay_rates[2] = float(np.clip(decay_rates[2] + 0.05 * metabolic_bias * dt_years, 0.005, 0.08))

        return x_post, P_post, innovation, innovation_norm, updated_decay_rates


class ClinicalCyberneticsEngine:
    """
    Public Service Engine providing real-time telemetry assimilation,
    dynamic state estimation, and instability alarming for the digital twin.
    """

    def __init__(self) -> None:
        self.ukf = UnscentedKalmanFilter()
        # Default baseline decay constants per organ
        self.default_decay = np.array([0.015, 0.012, 0.018, 0.008, 0.010, 0.012], dtype=np.float64)

    def assimilate_telemetry(self, req: CyberneticAssimilationRequest) -> CyberneticAssimilationResponse:
        """
        Assimilates a single real-time telemetry observation into the patient's continuous state space.
        """
        # 1. Parse prior state or initialize from population nominal baseline
        if req.prior_state:
            x_prior = np.array([req.prior_state.get(k, 80.0) for k in ORGAN_KEYS], dtype=np.float64)
        else:
            x_prior = np.array([85.0, 85.0, 85.0, 90.0, 88.0, 90.0], dtype=np.float64)

        if req.prior_covariance:
            variances = [req.prior_covariance.get(k, 25.0) for k in ORGAN_KEYS]
            P_prior = np.diag(variances).astype(np.float64)
        else:
            P_prior = np.diag([25.0, 25.0, 25.0, 20.0, 20.0, 20.0]).astype(np.float64)

        # 2. Assemble observation vector
        obs = req.observation
        y_obs = np.array([
            obs.heart_rate,
            obs.mean_arterial_pressure,
            obs.spo2,
            obs.blood_glucose,
            obs.egfr_proxy,
        ], dtype=np.float64)

        # Convert hours to years for longitudinal scale compatibility
        dt_years = req.elapsed_time_hours / 8760.0

        # 3. Execute UKF step
        x_post, P_post, innovation, inno_norm, updated_decay = self.ukf.filter_step(
            x_prior=x_prior,
            P_prior=P_prior,
            y_obs=y_obs,
            dt_years=dt_years,
            decay_rates=self.default_decay.copy(),
            interventions=req.active_interventions,
        )

        # 4. Format state estimates and standard deviations
        stds = np.sqrt(np.maximum(np.diag(P_post), 1e-4))
        reserves = {ORGAN_KEYS[i]: round(float(x_post[i]), 2) for i in range(NUM_STATES)}
        uncertainties = {ORGAN_KEYS[i]: round(float(stds[i]), 2) for i in range(NUM_STATES)}
        decay_dict = {ORGAN_KEYS[i]: round(float(updated_decay[i]), 4) for i in range(NUM_STATES)}

        # 5. Stability and Hemodynamic Alert Classification
        is_unstable = False
        alert_msg = None

        if obs.mean_arterial_pressure < 65.0:
            is_unstable = True
            alert_msg = "CRITICAL: Severe Hypotension / Circulatory Shock Risk (MAP < 65 mmHg)"
            stability = "CRITICAL_INSTABILITY"
        elif obs.spo2 < 90.0:
            is_unstable = True
            alert_msg = "CRITICAL: Hypoxemic Respiratory Decompensation (SpO2 < 90%)"
            stability = "CRITICAL_INSTABILITY"
        elif inno_norm > 45.0 or reserves["cardiovascular"] < 40.0:
            is_unstable = True
            alert_msg = "WARNING: Elevated filter innovation residual indicates acute physiological decompensation"
            stability = "COMPENSATED_STRESS"
        else:
            stability = "STABLE"

        sampling_interval = 10 if is_unstable else 60

        estimate = KalmanStateEstimate(
            estimated_organ_reserves=reserves,
            state_uncertainties_std=uncertainties,
            dynamic_decay_rates=decay_dict,
            filter_innovation_norm=round(inno_norm, 3),
            system_stability_status=stability,
        )

        return CyberneticAssimilationResponse(
            patient_id=req.patient_id,
            posterior_estimate=estimate,
            hemodynamic_instability_detected=is_unstable,
            recommended_sampling_interval_sec=sampling_interval,
            clinical_alert=alert_msg,
        )


cybernetics_engine = ClinicalCyberneticsEngine()
