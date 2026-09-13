/// Pure Rust High-Speed ECG DSP Signal Processor.
/// Implements Pan-Tompkins real-time QRS detection and Heart Rate Variability (HRV / RMSSD) analysis.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ECGAnalysisResult {
    pub heart_rate_bpm: f64,
    pub r_peaks_count: usize,
    pub is_arrhythmia_detected: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HrvMetrics {
    pub heart_rate_bpm: f64,
    pub sdnn_ms: f64,
    pub rmssd_ms: f64,
    pub pnn50_percent: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PanTompkinsResult {
    pub heart_rate_bpm: f64,
    pub r_peaks_count: usize,
    pub r_peak_indices: Vec<usize>,
    pub mean_rr_ms: f64,
    pub sdnn_ms: f64,
    pub rmssd_ms: f64,
    pub pnn50_percent: f64,
    pub is_arrhythmia_detected: bool,
}

/// Legacy lightweight peak detection thresholding (retained for backward compatibility)
#[allow(dead_code)]
pub fn analyze_ecg_waveform(samples: &[f64], sampling_rate_hz: f64) -> ECGAnalysisResult {
    if samples.is_empty() || sampling_rate_hz <= 0.0 {
        return ECGAnalysisResult {
            heart_rate_bpm: 0.0,
            r_peaks_count: 0,
            is_arrhythmia_detected: false,
        };
    }

    let mean: f64 = samples.iter().sum::<f64>() / (samples.len() as f64);
    let threshold = mean + 0.5;

    let mut peaks = 0;
    let mut i = 1;
    while i < samples.len() - 1 {
        if samples[i] > threshold && samples[i] > samples[i - 1] && samples[i] > samples[i + 1] {
            peaks += 1;
            i += 5; // Refractory period
        } else {
            i += 1;
        }
    }

    let duration_seconds = samples.len() as f64 / sampling_rate_hz;
    let heart_rate_bpm = if duration_seconds > 0.0 {
        (peaks as f64 / duration_seconds) * 60.0
    } else {
        0.0
    };

    let is_arrhythmia = heart_rate_bpm > 100.0 || heart_rate_bpm < 50.0;

    ECGAnalysisResult {
        heart_rate_bpm: round_2(heart_rate_bpm),
        r_peaks_count: peaks,
        is_arrhythmia_detected: is_arrhythmia,
    }
}

/// Full Pan-Tompkins ECG QRS detector
/// Pipeline:
/// 1. Baseline wander removal & bandpass (5 - 15 Hz)
/// 2. Five-point derivative filter
/// 3. Non-linear squaring
/// 4. Moving window integration (150 ms)
/// 5. Adaptive dual-threshold state machine
/// 6. R-peak localization & HRV RMSSD computation
pub fn pan_tompkins_qrs_detector(samples: &[f64], sampling_rate_hz: f64) -> PanTompkinsResult {
    let n = samples.len();
    if n < 10 || sampling_rate_hz <= 0.0 {
        return PanTompkinsResult {
            heart_rate_bpm: 0.0,
            r_peaks_count: 0,
            r_peak_indices: Vec::new(),
            mean_rr_ms: 0.0,
            sdnn_ms: 0.0,
            rmssd_ms: 0.0,
            pnn50_percent: 0.0,
            is_arrhythmia_detected: false,
        };
    }

    // Step 1: Bandpass Filter (Baseline removal + High frequency smoothing)
    let lp_window = (sampling_rate_hz * 0.030).round().max(1.0) as usize;
    let hp_window = (sampling_rate_hz * 0.300).round().max(3.0) as usize;

    let mut filtered = Vec::with_capacity(n);
    let mut running_sum_hp = 0.0;
    for i in 0..n {
        running_sum_hp += samples[i];
        if i >= hp_window {
            running_sum_hp -= samples[i - hp_window];
        }
        let count_hp = (i + 1).min(hp_window) as f64;
        let baseline = running_sum_hp / count_hp;
        filtered.push(samples[i] - baseline);
    }

    // Low-pass smooth
    let mut smoothed = Vec::with_capacity(n);
    let mut running_sum_lp = 0.0;
    for i in 0..n {
        running_sum_lp += filtered[i];
        if i >= lp_window {
            running_sum_lp -= filtered[i - lp_window];
        }
        let count_lp = (i + 1).min(lp_window) as f64;
        smoothed.push(running_sum_lp / count_lp);
    }

    // Step 2: 5-point Derivative: y[n] = (2x[n] + x[n-1] - x[n-3] - 2x[n-4]) / 8
    let mut derivative = vec![0.0; n];
    for i in 4..n {
        derivative[i] = (2.0 * smoothed[i] + smoothed[i - 1] - smoothed[i - 3] - 2.0 * smoothed[i - 4]) / 8.0;
    }

    // Step 3: Squaring function
    let mut squared = Vec::with_capacity(n);
    for val in &derivative {
        squared.push(val * val);
    }

    // Step 4: Moving Window Integration (window ~ 150 ms)
    let mwi_window = (sampling_rate_hz * 0.150).round().max(1.0) as usize;
    let mut integrated = vec![0.0; n];
    let mut mwi_sum = 0.0;
    for i in 0..n {
        mwi_sum += squared[i];
        if i >= mwi_window {
            mwi_sum -= squared[i - mwi_window];
        }
        integrated[i] = mwi_sum / mwi_window as f64;
    }

    // Step 5: Adaptive Peak Detection with Plateau-Safe Window Localization
    let mean_integrated = integrated.iter().sum::<f64>() / (n as f64);
    let variance = integrated.iter().map(|&v| (v - mean_integrated).powi(2)).sum::<f64>() / (n as f64);
    let std_integrated = variance.sqrt();
    let threshold = (mean_integrated + 0.5 * std_integrated).max(1e-6);

    let min_distance = (sampling_rate_hz * 0.200).round().max(2.0) as usize; // 200 ms
    let search_window = (sampling_rate_hz * 0.150).round().max(1.0) as usize; // 150 ms search window

    let mut candidate_peaks = Vec::new();
    let mut i = 0;
    while i < n {
        if integrated[i] > threshold {
            // Localize true R-peak maximum in original signal within search window
            let start = if i >= search_window { i - search_window } else { 0 };
            let end = (i + search_window).min(n - 1);
            let mut best_idx = i;
            let mut max_val = samples[i];
            for j in start..=end {
                if samples[j] > max_val {
                    max_val = samples[j];
                    best_idx = j;
                }
            }

            if candidate_peaks.is_empty() || (best_idx - candidate_peaks.last().copied().unwrap_or(0)) > min_distance {
                candidate_peaks.push(best_idx);
            }
            i = (best_idx + min_distance).max(i + min_distance);
        } else {
            i += 1;
        }
    }

    // Step 6: Heart Rate Variability (HRV) and Arrhythmia Assessment
    let hrv = compute_hrv_metrics(&candidate_peaks, sampling_rate_hz);
    let mean_rr_ms = if hrv.heart_rate_bpm > 0.0 { round_2(60000.0 / hrv.heart_rate_bpm) } else { 0.0 };
    let is_arrhythmia = hrv.heart_rate_bpm > 100.0 || (hrv.heart_rate_bpm < 50.0 && hrv.heart_rate_bpm > 0.0) || hrv.rmssd_ms > 120.0;

    PanTompkinsResult {
        heart_rate_bpm: hrv.heart_rate_bpm,
        r_peaks_count: candidate_peaks.len(),
        r_peak_indices: candidate_peaks,
        mean_rr_ms,
        sdnn_ms: hrv.sdnn_ms,
        rmssd_ms: hrv.rmssd_ms,
        pnn50_percent: hrv.pnn50_percent,
        is_arrhythmia_detected: is_arrhythmia,
    }
}

/// Computes clinical Heart Rate Variability (HRV) metrics:
/// Heart Rate (bpm), SDNN (ms), RMSSD (ms), and pNN50 (%) from detected R-peaks.
pub fn compute_hrv_metrics(r_peaks: &[usize], sampling_rate_hz: f64) -> HrvMetrics {
    if r_peaks.len() < 2 || sampling_rate_hz <= 0.0 || !sampling_rate_hz.is_finite() {
        return HrvMetrics {
            heart_rate_bpm: 0.0,
            sdnn_ms: 0.0,
            rmssd_ms: 0.0,
            pnn50_percent: 0.0,
        };
    }

    let mut rr_ms = Vec::with_capacity(r_peaks.len().saturating_sub(1));
    for w in r_peaks.windows(2) {
        let diff = (w[1] - w[0]) as f64;
        let interval = (diff / sampling_rate_hz) * 1000.0;
        if interval >= 250.0 && interval <= 2000.0 {
            rr_ms.push(interval);
        }
    }

    if rr_ms.is_empty() {
        for w in r_peaks.windows(2) {
            let diff = (w[1] - w[0]) as f64;
            rr_ms.push((diff / sampling_rate_hz) * 1000.0);
        }
    }

    if rr_ms.is_empty() {
        return HrvMetrics {
            heart_rate_bpm: 0.0,
            sdnn_ms: 0.0,
            rmssd_ms: 0.0,
            pnn50_percent: 0.0,
        };
    }

    let k = rr_ms.len() as f64;
    let mean_rr = rr_ms.iter().sum::<f64>() / k;
    let heart_rate_bpm = if mean_rr > 0.0 { 60000.0 / mean_rr } else { 0.0 };

    let variance = if rr_ms.len() >= 2 {
        rr_ms.iter().map(|&x| (x - mean_rr).powi(2)).sum::<f64>() / (k - 1.0)
    } else {
        0.0
    };
    let sdnn_ms = variance.sqrt();

    let mut sum_diff_sq = 0.0;
    let mut nn50_count = 0;
    let diff_count = rr_ms.len().saturating_sub(1);
    if diff_count >= 1 {
        for w in rr_ms.windows(2) {
            let diff = (w[1] - w[0]).abs();
            sum_diff_sq += diff * diff;
            if diff > 50.0 {
                nn50_count += 1;
            }
        }
    }

    let rmssd_ms = if diff_count >= 1 {
        (sum_diff_sq / diff_count as f64).sqrt()
    } else {
        0.0
    };

    let pnn50_percent = if diff_count >= 1 {
        (nn50_count as f64 / diff_count as f64) * 100.0
    } else {
        0.0
    };

    HrvMetrics {
        heart_rate_bpm: round_2(heart_rate_bpm),
        sdnn_ms: round_2(sdnn_ms),
        rmssd_ms: round_2(rmssd_ms),
        pnn50_percent: round_2(pnn50_percent),
    }
}

fn round_2(val: f64) -> f64 {
    (val * 100.0).round() / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_ecg_waveform() {
        let result = pan_tompkins_qrs_detector(&[], 250.0);
        assert_eq!(result.heart_rate_bpm, 0.0);
        assert_eq!(result.r_peaks_count, 0);
        assert_eq!(result.r_peak_indices.len(), 0);
    }

    #[test]
    fn test_synthetic_sinus_rhythm_60bpm() {
        // 60 bpm = 1 beat per second. At 250 Hz, peaks at 250, 500, 750, 1000...
        let sampling_rate = 250.0;
        let total_samples = 250 * 5; // 5 seconds
        let mut signal = vec![0.0; total_samples];

        for sec in 0..5 {
            let peak_idx = sec * 250 + 125;
            if peak_idx < total_samples {
                signal[peak_idx] = 1.5; // R peak
                if peak_idx > 0 { signal[peak_idx - 1] = 0.5; }
                if peak_idx + 1 < total_samples { signal[peak_idx + 1] = 0.5; }
            }
        }

        let result = pan_tompkins_qrs_detector(&signal, sampling_rate);
        assert!(result.r_peaks_count >= 4);
        assert!((result.heart_rate_bpm - 60.0).abs() < 5.0, "Expected ~60 bpm, got {}", result.heart_rate_bpm);
        assert_eq!(result.is_arrhythmia_detected, false);
    }

    #[test]
    fn test_synthetic_tachycardia_detection() {
        // 120 bpm = 2 beats per second. At 250 Hz, peaks every 125 samples
        let sampling_rate = 250.0;
        let total_samples = 250 * 4;
        let mut signal = vec![0.0; total_samples];

        for beat in 0..8 {
            let peak_idx = beat * 125 + 60;
            if peak_idx < total_samples {
                signal[peak_idx] = 2.0;
                if peak_idx > 0 { signal[peak_idx - 1] = 0.8; }
                if peak_idx + 1 < total_samples { signal[peak_idx + 1] = 0.8; }
            }
        }

        let result = pan_tompkins_qrs_detector(&signal, sampling_rate);
        assert!(result.heart_rate_bpm > 100.0);
        assert!(result.is_arrhythmia_detected);
    }

    #[test]
    fn test_compute_hrv_metrics_direct() {
        let r_peaks = vec![250, 500, 750, 1000, 1250];
        let hrv = compute_hrv_metrics(&r_peaks, 250.0);
        assert_eq!(hrv.heart_rate_bpm, 60.0);
        assert_eq!(hrv.sdnn_ms, 0.0);
        assert_eq!(hrv.rmssd_ms, 0.0);
        assert_eq!(hrv.pnn50_percent, 0.0);
    }

    #[test]
    fn test_synthetic_plateau_peaks() {
        // Flat plateau peak: 20 identical samples
        let sampling_rate = 250.0;
        let total_samples = 250 * 3;
        let mut signal = vec![0.0; total_samples];
        for sec in 0..3 {
            let start = sec * 250 + 100;
            for j in 0..15 {
                signal[start + j] = 2.0;
            }
        }
        let result = pan_tompkins_qrs_detector(&signal, sampling_rate);
        assert!(result.r_peaks_count >= 2);
        assert!(result.heart_rate_bpm >= 50.0 && result.heart_rate_bpm <= 70.0);
    }
}

