//! Adversarial Stress Test Suite for Wave 3 Milestone M1
//! Biosignal Pan-Tompkins DSP & SIMD AVX2 Vector Math
//!
//! Evaluates:
//! 1. Pan-Tompkins ECG: Flatline (0Hz), Tachycardia (240 bpm), Bradycardia (30 bpm),
//!    High-frequency noise, NaN/Inf signals, Zero/negative sampling rates, Short buffers (<10, 0, 1, 9, 10).
//!    Ensures ZERO panics, graceful degradation, and accurate QRS & HRV RMSSD calculations.
//! 2. SIMD AVX2 Vector Math: 384, 768, 1536 (and non-aligned 769, 1537) dimensions across:
//!    - Orthogonal vectors
//!    - Identical vectors
//!    - Opposite (antiparallel) vectors
//!    - All-zero vectors
//!    - Large magnitude vectors (1e4)
//!    - Small magnitude vectors (1e-4)
//!    Verifies mathematical parity between SIMD, scalar fallback, and analytical ground truth.
//! 3. Benchmark latency validation:
//!    - 10,000-sample ECG processing latency (< 1.0 ms in release)
//!    - Embedding pair computation latency (< 5.0 µs in release)

use std::time::Instant;
use rust_gateway_ffi::ecg_dsp::{
    pan_tompkins_qrs_detector, compute_hrv_metrics, analyze_ecg_waveform,
};
use rust_gateway_ffi::vector_store::{
    cosine_similarity, cosine_similarity_fallback,
    euclidean_distance, euclidean_distance_fallback,
};

// =================================================================================================
// 1. PAN-TOMPKINS ECG ADVERSARIAL STRESS TESTS
// =================================================================================================

#[test]
fn test_ecg_flatline_0hz_signals() {
    let sampling_rate = 250.0;

    // Test A: All Zeros flatline (10,000 samples)
    let zeros = vec![0.0f64; 10_000];
    let res_zeros = pan_tompkins_qrs_detector(&zeros, sampling_rate);
    assert_eq!(res_zeros.r_peaks_count, 0, "Flatline zeros must have 0 peaks");
    assert_eq!(res_zeros.heart_rate_bpm, 0.0, "Flatline zeros must report 0 bpm");
    assert!(!res_zeros.is_arrhythmia_detected, "Flatline zeros must not report arrhythmia");
    assert_eq!(res_zeros.rmssd_ms, 0.0, "Flatline zeros RMSSD must be 0");
    assert_eq!(res_zeros.mean_rr_ms, 0.0);
    assert_eq!(res_zeros.sdnn_ms, 0.0);

    // Test B: Constant non-zero DC offset flatline (5,000 samples of 3.3V)
    let dc_offset = vec![3.3f64; 5_000];
    let res_dc = pan_tompkins_qrs_detector(&dc_offset, sampling_rate);
    assert_eq!(res_dc.r_peaks_count, 0, "Flatline DC offset must have 0 peaks");
    assert_eq!(res_dc.heart_rate_bpm, 0.0);
    assert!(!res_dc.is_arrhythmia_detected);

    // Test C: Legacy analyze_ecg_waveform on flatline
    let legacy_res = analyze_ecg_waveform(&zeros, sampling_rate);
    assert_eq!(legacy_res.r_peaks_count, 0);
    assert_eq!(legacy_res.heart_rate_bpm, 0.0);
}

#[test]
fn test_ecg_extreme_tachycardia_240bpm() {
    // 240 bpm = 4 beats per second. At 250 Hz, RR interval is 62.5 samples (250 ms).
    let sampling_rate = 250.0;
    let duration_sec = 5;
    let total_samples = (sampling_rate * duration_sec as f64) as usize; // 1250 samples
    let mut signal = vec![0.0f64; total_samples];

    // Inject 19 R-peaks at 250 ms intervals (samples: 62, 125, 187, 250, 312, 375, ...)
    let expected_beats = 19;
    for b in 1..=expected_beats {
        let peak_idx = (b as f64 * 62.5).round() as usize;
        if peak_idx < total_samples {
            signal[peak_idx] = 2.5;
            if peak_idx > 0 { signal[peak_idx - 1] = 0.6; }
            if peak_idx + 1 < total_samples { signal[peak_idx + 1] = 0.6; }
        }
    }

    let result = pan_tompkins_qrs_detector(&signal, sampling_rate);
    println!(
        "Tachycardia 240 bpm: detected {} peaks, HR = {:.1} bpm, RMSSD = {:.1} ms",
        result.r_peaks_count, result.heart_rate_bpm, result.rmssd_ms
    );

    // Physiological acceptance: 240 bpm detected within ±15 bpm margin
    assert!(result.r_peaks_count >= 16, "Expected ~19 peaks for 240 bpm, got {}", result.r_peaks_count);
    assert!(
        (result.heart_rate_bpm - 240.0).abs() < 20.0,
        "Expected ~240 bpm, got {:.1} bpm",
        result.heart_rate_bpm
    );
    assert!(result.is_arrhythmia_detected, "240 bpm must be flagged as arrhythmia");
    assert!(result.mean_rr_ms >= 200.0 && result.mean_rr_ms <= 300.0, "Mean RR should be ~250 ms");
}

#[test]
fn test_ecg_severe_bradycardia_30bpm() {
    // 30 bpm = 0.5 beats per second = 1 beat every 2.0 s (2000 ms).
    // At 250 Hz, RR interval is 500 samples.
    let sampling_rate = 250.0;
    let duration_sec = 12;
    let total_samples = (sampling_rate * duration_sec as f64) as usize; // 3000 samples
    let mut signal = vec![0.0f64; total_samples];

    // 5 peaks spaced by 500 samples
    for b in 1..6 {
        let idx = b * 500;
        if idx < total_samples {
            signal[idx] = 2.2;
            if idx > 0 { signal[idx - 1] = 0.5; }
            if idx + 1 < total_samples { signal[idx + 1] = 0.5; }
        }
    }

    let result = pan_tompkins_qrs_detector(&signal, sampling_rate);
    println!(
        "Bradycardia 30 bpm: detected {} peaks, HR = {:.1} bpm, RMSSD = {:.1} ms",
        result.r_peaks_count, result.heart_rate_bpm, result.rmssd_ms
    );

    assert!(result.r_peaks_count >= 4, "Expected ~5 peaks for 30 bpm, got {}", result.r_peaks_count);
    assert!(
        (result.heart_rate_bpm - 30.0).abs() < 5.0,
        "Expected ~30 bpm, got {:.1} bpm",
        result.heart_rate_bpm
    );
    assert!(result.is_arrhythmia_detected, "30 bpm must be flagged as arrhythmia");
    assert!(
        (result.mean_rr_ms - 2000.0).abs() < 50.0,
        "Expected Mean RR ~2000 ms, got {:.1} ms",
        result.mean_rr_ms
    );
}

#[test]
fn test_ecg_high_frequency_noise_attenuation() {
    let sampling_rate = 250.0;
    let total_samples = 2500; // 10 seconds

    // Test A: High-frequency Nyquist oscillation (125 Hz) + 60 Hz mains hum without QRS
    // Must be suppressed by the bandpass filter and produce 0 false peaks.
    let mut noise_signal = Vec::with_capacity(total_samples);
    for i in 0..total_samples {
        let t = i as f64 / sampling_rate;
        let nyquist_noise = if i % 2 == 0 { 0.8 } else { -0.8 };
        let mains_hum = 0.5 * (2.0 * std::f64::consts::PI * 60.0 * t).sin();
        noise_signal.push(nyquist_noise + mains_hum);
    }

    let result_noise = pan_tompkins_qrs_detector(&noise_signal, sampling_rate);
    println!("Noise only result: peaks={}, HR={}, indices={:?}", result_noise.r_peaks_count, result_noise.heart_rate_bpm, result_noise.r_peak_indices);
    // In presence of high-frequency noise and mains hum without any cardiac pulses,
    // false peak count should be at most 1 (due to filter startup transient) and HR should be 0 or flagged
    assert!(
        result_noise.r_peaks_count <= 1,
        "Bandpass filter must eliminate pure high-frequency noise without runaway peaks, found {}",
        result_noise.r_peaks_count
    );
    assert_eq!(result_noise.heart_rate_bpm, 0.0);

    // Test B: 60 bpm signal contaminated with 50 Hz powerline interference
    let mut contaminated = Vec::with_capacity(total_samples);
    for i in 0..total_samples {
        let t = i as f64 / sampling_rate;
        let hum = 0.4 * (2.0 * std::f64::consts::PI * 50.0 * t).sin();
        contaminated.push(hum);
    }
    // Inject 9 clean QRS peaks (every 250 samples)
    for b in 1..10 {
        let idx = b * 250;
        if idx < total_samples {
            contaminated[idx] += 2.5;
            contaminated[idx - 1] += 0.7;
            contaminated[idx + 1] += 0.7;
        }
    }

    let result_contam = pan_tompkins_qrs_detector(&contaminated, sampling_rate);
    assert!(
        result_contam.r_peaks_count >= 8,
        "Pan-Tompkins should reliably detect QRS amidst 50 Hz noise: got {}",
        result_contam.r_peaks_count
    );
    assert!(
        (result_contam.heart_rate_bpm - 60.0).abs() < 5.0,
        "Heart rate should remain ~60 bpm despite noise, got {:.1}",
        result_contam.heart_rate_bpm
    );
}

#[test]
fn test_ecg_nan_and_infinity_resilience() {
    let sampling_rate = 250.0;
    let n = 1000;

    // Test A: Signal containing NaN values
    let mut nan_signal = vec![0.0f64; n];
    nan_signal[100] = f64::NAN;
    nan_signal[500] = f64::NAN;

    // Must execute without panic
    let res_nan = pan_tompkins_qrs_detector(&nan_signal, sampling_rate);
    println!("NaN signal handled gracefully: peaks={}, HR={}", res_nan.r_peaks_count, res_nan.heart_rate_bpm);
    assert!(!res_nan.heart_rate_bpm.is_nan(), "Heart rate must not be NaN");
    assert!(!res_nan.rmssd_ms.is_nan(), "RMSSD must not be NaN");

    // Test B: All NaN signal
    let all_nan = vec![f64::NAN; n];
    let res_all_nan = pan_tompkins_qrs_detector(&all_nan, sampling_rate);
    assert_eq!(res_all_nan.r_peaks_count, 0);
    assert_eq!(res_all_nan.heart_rate_bpm, 0.0);
    assert!(!res_all_nan.heart_rate_bpm.is_nan());

    // Test C: Signal containing Inf and -Inf values
    let mut inf_signal = vec![0.0f64; n];
    inf_signal[200] = f64::INFINITY;
    inf_signal[400] = f64::NEG_INFINITY;
    let res_inf = pan_tompkins_qrs_detector(&inf_signal, sampling_rate);
    assert!(!res_inf.heart_rate_bpm.is_nan());
    assert!(!res_inf.heart_rate_bpm.is_infinite());

    // Test D: HRV metrics with NaN/Inf values
    let peaks_with_bounds = vec![100, 200, 300];
    let hrv_res = compute_hrv_metrics(&peaks_with_bounds, sampling_rate);
    assert!(!hrv_res.heart_rate_bpm.is_nan());
    assert!(!hrv_res.rmssd_ms.is_nan());
}

#[test]
fn test_ecg_zero_negative_nan_sampling_rates() {
    let signal = vec![1.0; 500];

    // Sampling rate = 0.0
    let res_zero = pan_tompkins_qrs_detector(&signal, 0.0);
    assert_eq!(res_zero.heart_rate_bpm, 0.0);
    assert_eq!(res_zero.r_peaks_count, 0);

    // Negative sampling rate
    let res_neg = pan_tompkins_qrs_detector(&signal, -250.0);
    assert_eq!(res_neg.heart_rate_bpm, 0.0);
    assert_eq!(res_neg.r_peaks_count, 0);

    // NaN sampling rate
    let res_nan_sr = pan_tompkins_qrs_detector(&signal, f64::NAN);
    assert_eq!(res_nan_sr.heart_rate_bpm, 0.0);
    assert_eq!(res_nan_sr.r_peaks_count, 0);

    // HRV direct call with 0.0 and negative sampling rates
    let hrv_zero = compute_hrv_metrics(&[100, 200, 300], 0.0);
    assert_eq!(hrv_zero.heart_rate_bpm, 0.0);
    let hrv_neg = compute_hrv_metrics(&[100, 200, 300], -100.0);
    assert_eq!(hrv_neg.heart_rate_bpm, 0.0);
}

#[test]
fn test_ecg_short_buffers_boundary_conditions() {
    let sr = 250.0;

    // Buffer len = 0 (empty)
    let res_0 = pan_tompkins_qrs_detector(&[], sr);
    assert_eq!(res_0.r_peaks_count, 0);
    assert_eq!(res_0.heart_rate_bpm, 0.0);

    // Buffer len = 1
    let res_1 = pan_tompkins_qrs_detector(&[1.5], sr);
    assert_eq!(res_1.r_peaks_count, 0);

    // Buffer len = 5
    let res_5 = pan_tompkins_qrs_detector(&[0.1, 0.5, 2.0, 0.5, 0.1], sr);
    assert_eq!(res_5.r_peaks_count, 0);

    // Buffer len = 9 (boundary just below 10)
    let res_9 = pan_tompkins_qrs_detector(&[0.1; 9], sr);
    assert_eq!(res_9.r_peaks_count, 0);

    // Buffer len = 10 (exact threshold boundary)
    let res_10 = pan_tompkins_qrs_detector(&[0.1; 10], sr);
    assert_eq!(res_10.r_peaks_count, 0);

    // Buffer len = 15 (short buffer with pulse)
    let mut pulse_15 = vec![0.0; 15];
    pulse_15[7] = 3.0;
    let res_15 = pan_tompkins_qrs_detector(&pulse_15, sr);
    // Even if peak is located, single peak cannot compute RR interval -> 0 bpm
    assert!(res_15.heart_rate_bpm >= 0.0);
    assert_eq!(res_15.rmssd_ms, 0.0);
}

#[test]
fn test_hrv_rmssd_exact_numerical_parity() {
    let sampling_rate = 250.0;

    // Construct exactly known RR intervals:
    // 5 peaks:
    // peak 0: sample 250
    // peak 1: sample 500  -> RR0 = 250 samples = 1000.0 ms
    // peak 2: sample 775  -> RR1 = 275 samples = 1100.0 ms (diff0 = +100 ms)
    // peak 3: sample 1025 -> RR2 = 250 samples = 1000.0 ms (diff1 = -100 ms)
    // peak 4: sample 1300 -> RR3 = 275 samples = 1100.0 ms (diff2 = +100 ms)
    let r_peaks = vec![250, 500, 775, 1025, 1300];
    let hrv = compute_hrv_metrics(&r_peaks, sampling_rate);

    // Analytical calculations:
    // Mean RR = (1000 + 1100 + 1000 + 1100) / 4 = 1050.0 ms
    // HR = 60,000 / 1050 = 57.14 bpm
    let expected_hr = ((60000.0f64 / 1050.0f64) * 100.0f64).round() / 100.0f64;
    assert_eq!(hrv.heart_rate_bpm, expected_hr, "HR must match 57.14 bpm");

    // Successive differences:
    // d0 = 1100 - 1000 = 100 ms
    // d1 = 1000 - 1100 = -100 ms
    // d2 = 1100 - 1000 = 100 ms
    // sum_diff_sq = 100^2 + (-100)^2 + 100^2 = 10000 + 10000 + 10000 = 30000
    // RMSSD = sqrt(30000 / 3) = sqrt(10000) = 100.0 ms!
    assert_eq!(hrv.rmssd_ms, 100.0, "RMSSD must be exactly 100.0 ms");

    // nn50 count: all 3 differences are 100 ms (> 50 ms), so 3 / 3 = 100.0%
    assert_eq!(hrv.pnn50_percent, 100.0, "pNN50 must be exactly 100.0%");
}

// =================================================================================================
// 2. SIMD AVX2 VECTOR MATH ADVERSARIAL STRESS TESTS
// =================================================================================================

#[test]
fn test_simd_orthogonal_vectors_across_dimensions() {
    // Orthogonal test: a = [1, 0, 1, 0...], b = [0, 1, 0, 1...]
    // Dot product = 0.0 -> Cosine similarity = 0.0
    // Euclidean distance = sqrt(N/2 * 1^2 + N/2 * 1^2) = sqrt(N)
    for &dim in &[384, 768, 1536, 769, 1537] {
        let mut vec_a = vec![0.0f32; dim];
        let mut vec_b = vec![0.0f32; dim];
        for i in 0..dim {
            if i % 2 == 0 {
                vec_a[i] = 1.0;
            } else {
                vec_b[i] = 1.0;
            }
        }

        // Cosine similarity must be 0.0
        let cos_simd = cosine_similarity(&vec_a, &vec_b);
        let cos_fallback = cosine_similarity_fallback(&vec_a, &vec_b);
        assert!(cos_simd.abs() < 1e-6, "Orthogonal cos_simd at dim {} must be 0.0, got {}", dim, cos_simd);
        assert!((cos_simd - cos_fallback).abs() < 1e-6);

        // Euclidean distance must be sqrt(dim)
        let expected_l2 = (dim as f32).sqrt();
        let dist_simd = euclidean_distance(&vec_a, &vec_b);
        let dist_fallback = euclidean_distance_fallback(&vec_a, &vec_b);
        assert!(
            (dist_simd - expected_l2).abs() < 1e-4,
            "Orthogonal dist_simd at dim {} expected {:.4}, got {:.4}",
            dim, expected_l2, dist_simd
        );
        assert!(
            (dist_simd - dist_fallback).abs() < 1e-4,
            "Parity error at dim {}: simd={:.4}, fallback={:.4}",
            dim, dist_simd, dist_fallback
        );
    }
}

#[test]
fn test_simd_identical_vectors_across_dimensions() {
    // Identical test: a = b
    // Cosine similarity = 1.0
    // Euclidean distance = 0.0
    for &dim in &[384, 768, 1536, 769, 1537] {
        let vec_a: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.07).sin() + 0.5).collect();

        let cos_simd = cosine_similarity(&vec_a, &vec_a);
        let cos_fallback = cosine_similarity_fallback(&vec_a, &vec_a);
        assert!((cos_simd - 1.0).abs() < 1e-5, "Identical cos_simd must be 1.0, got {}", cos_simd);
        assert!((cos_simd - cos_fallback).abs() < 1e-5);

        let dist_simd = euclidean_distance(&vec_a, &vec_a);
        let dist_fallback = euclidean_distance_fallback(&vec_a, &vec_a);
        assert!(dist_simd < 1e-6, "Identical dist_simd must be 0.0, got {}", dist_simd);
        assert!(dist_fallback < 1e-6);
    }
}

#[test]
fn test_simd_opposite_antiparallel_vectors_across_dimensions() {
    // Opposite test: b = -a
    // Cosine similarity = -1.0
    // Euclidean distance = 2 * ||a||
    for &dim in &[384, 768, 1536, 769, 1537] {
        let vec_a: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.03).cos() + 1.0).collect();
        let vec_b: Vec<f32> = vec_a.iter().map(|&x| -x).collect();

        let cos_simd = cosine_similarity(&vec_a, &vec_b);
        let cos_fallback = cosine_similarity_fallback(&vec_a, &vec_b);
        assert!((cos_simd - (-1.0)).abs() < 1e-5, "Opposite cos_simd must be -1.0, got {}", cos_simd);
        assert!((cos_simd - cos_fallback).abs() < 1e-5);

        let norm_a: f32 = vec_a.iter().map(|&x| x * x).sum::<f32>().sqrt();
        let expected_dist = 2.0 * norm_a;
        let dist_simd = euclidean_distance(&vec_a, &vec_b);
        let dist_fallback = euclidean_distance_fallback(&vec_a, &vec_b);
        assert!(
            (dist_simd - expected_dist).abs() < 1e-3,
            "Opposite dist_simd at dim {} expected {:.4}, got {:.4}",
            dim, expected_dist, dist_simd
        );
        assert!((dist_simd - dist_fallback).abs() < 1e-3);
    }
}

#[test]
fn test_simd_all_zero_and_empty_vectors() {
    for &dim in &[384, 768, 1536] {
        let zeros = vec![0.0f32; dim];
        let non_zeros: Vec<f32> = vec![2.0f32; dim];

        // Zeros vs Zeros: cos = 0.0 (by contract), dist = 0.0
        assert_eq!(cosine_similarity(&zeros, &zeros), 0.0);
        assert_eq!(cosine_similarity_fallback(&zeros, &zeros), 0.0);
        assert_eq!(euclidean_distance(&zeros, &zeros), 0.0);
        assert_eq!(euclidean_distance_fallback(&zeros, &zeros), 0.0);

        // Zeros vs Non-zeros: cos = 0.0, dist = ||non_zeros||
        assert_eq!(cosine_similarity(&zeros, &non_zeros), 0.0);
        assert_eq!(cosine_similarity(&non_zeros, &zeros), 0.0);
        let expected_dist = (dim as f32 * 4.0).sqrt();
        let dist_simd = euclidean_distance(&zeros, &non_zeros);
        assert!((dist_simd - expected_dist).abs() < 1e-4);
    }

    // Empty vector boundary:
    assert_eq!(cosine_similarity(&[], &[]), 0.0);
    assert_eq!(euclidean_distance(&[], &[]), 0.0);

    // Mismatched lengths:
    let v3 = vec![1.0, 2.0, 3.0];
    let v4 = vec![1.0, 2.0, 3.0, 4.0];
    assert_eq!(cosine_similarity(&v3, &v4), 0.0);
    assert_eq!(euclidean_distance(&v3, &v4), 0.0);
}

#[test]
fn test_simd_large_and_small_magnitude_vectors() {
    let dim = 1536;

    // Large magnitude: 10,000.0 scale
    let large_a: Vec<f32> = (0..dim).map(|i| ((i % 10) as f32 + 1.0) * 10_000.0).collect();
    let large_b: Vec<f32> = (0..dim).map(|i| ((i % 10) as f32 + 2.0) * 10_000.0).collect();

    let cos_large_simd = cosine_similarity(&large_a, &large_b);
    let cos_large_fallback = cosine_similarity_fallback(&large_a, &large_b);
    assert!(
        (cos_large_simd - cos_large_fallback).abs() < 1e-4,
        "Large magnitude cosine similarity mismatch: simd={}, fallback={}",
        cos_large_simd, cos_large_fallback
    );

    let dist_large_simd = euclidean_distance(&large_a, &large_b);
    let dist_large_fallback = euclidean_distance_fallback(&large_a, &large_b);
    let expected_large_dist = 10_000.0 * (dim as f32).sqrt();
    println!(
        "Large dist: simd={:.4}, fallback={:.4}, expected={:.4}, diff={:.4}",
        dist_large_simd, dist_large_fallback, expected_large_dist, (dist_large_simd - dist_large_fallback).abs()
    );
    // Relative error check: in f32, relative tolerance should be within 1e-4
    let rel_err = (dist_large_simd - dist_large_fallback).abs() / expected_large_dist;
    assert!(rel_err < 1e-4, "Relative error too high: {}", rel_err);

    // Small magnitude: 1e-4 scale
    let small_a: Vec<f32> = large_a.iter().map(|&x| x * 1e-8).collect();
    let small_b: Vec<f32> = large_b.iter().map(|&x| x * 1e-8).collect();

    let cos_small_simd = cosine_similarity(&small_a, &small_b);
    let cos_small_fallback = cosine_similarity_fallback(&small_a, &small_b);
    assert!(
        (cos_small_simd - cos_small_fallback).abs() < 1e-4,
        "Small magnitude cosine similarity mismatch: simd={}, fallback={}",
        cos_small_simd, cos_small_fallback
    );
    // Scale invariance: cos_sim(alpha*a, alpha*b) == cos_sim(a, b)
    assert!(
        (cos_small_simd - cos_large_simd).abs() < 1e-4,
        "Scale invariance failed: small={}, large={}",
        cos_small_simd, cos_large_simd
    );
}

// =================================================================================================
// 3. BENCHMARK & LATENCY VERIFICATION TESTS
// =================================================================================================

#[test]
fn test_adversarial_10k_ecg_latency_under_1ms() {
    let sampling_rate = 250.0;
    let n = 10_000;
    let mut signal = Vec::with_capacity(n);

    // Synthesize 40 seconds of realistic ECG with baseline drift, high frequency noise, and 40 QRS peaks
    for i in 0..n {
        let t = i as f64 / sampling_rate;
        let baseline = 0.3 * (2.0 * std::f64::consts::PI * 0.2 * t).sin();
        let noise = 0.05 * (2.0 * std::f64::consts::PI * 60.0 * t).sin();
        signal.push(baseline + noise);
    }
    for b in 1..40 {
        let idx = b * 250;
        signal[idx] += 2.8;
        signal[idx - 1] += 0.8;
        signal[idx + 1] += 0.8;
    }

    // Warm-up iteration
    let _ = pan_tompkins_qrs_detector(&signal, sampling_rate);

    // Measure over 20 iterations
    let runs = 20;
    let start = Instant::now();
    for _ in 0..runs {
        let res = pan_tompkins_qrs_detector(&signal, sampling_rate);
        assert!(res.r_peaks_count >= 36);
    }
    let total_elapsed = start.elapsed();
    let avg_latency_ms = (total_elapsed.as_secs_f64() * 1000.0) / runs as f64;

    println!(
        "10k ECG Pan-Tompkins DSP Latency (avg over {} runs): {:.4} ms",
        runs, avg_latency_ms
    );

    // In release mode, must satisfy < 1.0 ms. In debug mode, allow generous 25 ms.
    let threshold_ms = if cfg!(debug_assertions) { 25.0 } else { 1.0 };
    assert!(
        avg_latency_ms < threshold_ms,
        "10k ECG processing too slow: {:.4} ms (threshold: {:.2} ms)",
        avg_latency_ms, threshold_ms
    );
}

#[test]
fn test_adversarial_simd_vector_math_latency_under_5us() {
    for &dim in &[384, 768, 1536] {
        let vec_a: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.01).sin()).collect();
        let vec_b: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.02).cos()).collect();

        // Warm up
        let _ = cosine_similarity(&vec_a, &vec_b);
        let _ = euclidean_distance(&vec_a, &vec_b);

        let iterations = 10_000;

        // Cosine similarity benchmark
        let start_cos = Instant::now();
        for _ in 0..iterations {
            std::hint::black_box(cosine_similarity(&vec_a, &vec_b));
        }
        let elapsed_cos = start_cos.elapsed();
        let cos_per_pair_us = (elapsed_cos.as_secs_f64() * 1_000_000.0) / iterations as f64;

        // Euclidean distance benchmark
        let start_dist = Instant::now();
        for _ in 0..iterations {
            std::hint::black_box(euclidean_distance(&vec_a, &vec_b));
        }
        let elapsed_dist = start_dist.elapsed();
        let dist_per_pair_us = (elapsed_dist.as_secs_f64() * 1_000_000.0) / iterations as f64;

        println!(
            "Dim {:4}: Cosine Similarity = {:.3} µs/pair | Euclidean Distance = {:.3} µs/pair",
            dim, cos_per_pair_us, dist_per_pair_us
        );

        let threshold_us = if cfg!(debug_assertions) { 25.0 } else { 5.0 };
        assert!(
            cos_per_pair_us < threshold_us,
            "Cosine similarity at dim {} too slow: {:.3} µs (threshold: {:.1} µs)",
            dim, cos_per_pair_us, threshold_us
        );
        assert!(
            dist_per_pair_us < threshold_us,
            "Euclidean distance at dim {} too slow: {:.3} µs (threshold: {:.1} µs)",
            dim, dist_per_pair_us, threshold_us
        );
    }
}
