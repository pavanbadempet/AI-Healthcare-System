/// Pure Rust High-Speed ECG DSP Signal Processor.
/// Analyzes 500Hz streaming ECG waveforms for R-peak detection & Heart Rate calculation.

#[allow(dead_code)]
pub struct ECGAnalysisResult {
    pub heart_rate_bpm: f64,
    pub r_peaks_count: usize,
    pub is_arrhythmia_detected: bool,
}

#[allow(dead_code)]
pub fn analyze_ecg_waveform(samples: &[f64], sampling_rate_hz: f64) -> ECGAnalysisResult {
    if samples.is_empty() || sampling_rate_hz <= 0.0 {
        return ECGAnalysisResult {
            heart_rate_bpm: 0.0,
            r_peaks_count: 0,
            is_arrhythmia_detected: false,
        };
    }

    // Peak detection thresholding
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

fn round_2(val: f64) -> f64 {
    (val * 100.0).round() / 100.0
}
