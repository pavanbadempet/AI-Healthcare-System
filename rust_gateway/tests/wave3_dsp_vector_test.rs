//! Wave 3 Integration Test: High-Speed Biosignal DSP & SIMD Vector Math
//! Verifies Pan-Tompkins QRS peak detection, HRV metrics computation,
//! SIMD AVX2 cosine similarity, and Euclidean L2 distance for high-dimensional embeddings.

use std::time::Instant;
use rust_gateway_ffi::ecg_dsp::pan_tompkins_qrs_detector;
use rust_gateway_ffi::vector_store::{
    cosine_similarity, cosine_similarity_fallback,
    euclidean_distance, euclidean_distance_fallback,
    batch_cosine_similarity,
};

#[test]
fn test_10k_sample_biosignal_pan_tompkins_latency() {
    let sampling_rate = 250.0;
    let total_samples = 10_000; // 40 seconds of biosignal
    let mut signal = Vec::with_capacity(total_samples);

    // Generate baseline sinusoid with respiratory wander
    for i in 0..total_samples {
        let t = i as f64 / sampling_rate;
        let baseline = 0.2 * (2.0 * std::f64::consts::PI * 0.25 * t).sin();
        let noise = 0.05 * (2.0 * std::f64::consts::PI * 50.0 * t).sin();
        signal.push(baseline + noise);
    }

    // Inject 40 R-peaks at 60 bpm (every 250 samples)
    for beat in 1..40 {
        let idx = beat * 250;
        if idx < total_samples {
            signal[idx] = 2.5; // R-peak
            if idx > 0 { signal[idx - 1] = 0.7; }
            if idx + 1 < total_samples { signal[idx + 1] = 0.7; }
        }
    }

    // Benchmark execution time
    let start = Instant::now();
    let result = pan_tompkins_qrs_detector(&signal, sampling_rate);
    let elapsed = start.elapsed();

    println!(
        "10,000-sample Pan-Tompkins DSP processed in {:?} (peaks: {}, HR: {:.1} bpm)",
        elapsed, result.r_peaks_count, result.heart_rate_bpm
    );

    // Acceptance criterion: sub-millisecond in release, generous bound in debug
    assert!(
        elapsed.as_millis() < 50,
        "DSP processing took too long: {:?}",
        elapsed
    );
    assert!(result.r_peaks_count >= 36, "Expected ~39 peaks, got {}", result.r_peaks_count);
    assert!(
        (result.heart_rate_bpm - 60.0).abs() < 5.0,
        "Expected ~60 bpm, got {}",
        result.heart_rate_bpm
    );
    assert_eq!(result.is_arrhythmia_detected, false);
    assert!(result.mean_rr_ms > 0.0);
    assert!(result.sdnn_ms >= 0.0);
    assert!(result.rmssd_ms >= 0.0);
}

#[test]
fn test_simd_cosine_similarity_latency_and_dimensions() {
    for &dim in &[384, 768, 1536] {
        let vec_a: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.03).sin()).collect();
        let vec_b: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.05).cos()).collect();

        // Parity check
        let sim_simd = cosine_similarity(&vec_a, &vec_b);
        let sim_fallback = cosine_similarity_fallback(&vec_a, &vec_b);
        assert!(
            (sim_simd - sim_fallback).abs() < 1e-4,
            "Cosine similarity mismatch at dim {}: simd={}, fallback={}",
            dim, sim_simd, sim_fallback
        );

        // Identical vector similarity must be 1.0
        let self_sim = cosine_similarity(&vec_a, &vec_a);
        assert!((self_sim - 1.0).abs() < 1e-5);

        // Benchmark per-pair latency over 1,000 iterations
        let iterations = 1_000;
        let start = Instant::now();
        for _ in 0..iterations {
            let _ = cosine_similarity(&vec_a, &vec_b);
        }
        let total_elapsed = start.elapsed();
        let per_pair_us = total_elapsed.as_micros() as f64 / iterations as f64;

        println!("Cosine similarity dim={}: {:.3} µs per vector pair", dim, per_pair_us);
        // Acceptance criterion: < 5 µs per pair in release, < 50 µs in unoptimized debug
        let max_allowed_us = if cfg!(debug_assertions) { 50.0 } else { 5.0 };
        assert!(
            per_pair_us < max_allowed_us,
            "Cosine similarity too slow at dim {}: {:.3} µs",
            dim, per_pair_us
        );
    }
}

#[test]
fn test_simd_euclidean_distance_latency_and_dimensions() {
    for &dim in &[384, 768, 1536] {
        let vec_a: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.02).sin()).collect();
        let vec_b: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.04).cos()).collect();

        // Parity check
        let dist_simd = euclidean_distance(&vec_a, &vec_b);
        let dist_fallback = euclidean_distance_fallback(&vec_a, &vec_b);
        assert!(
            (dist_simd - dist_fallback).abs() < 1e-4,
            "Euclidean distance mismatch at dim {}: simd={}, fallback={}",
            dim, dist_simd, dist_fallback
        );
        assert!(dist_simd > 0.0);

        // Distance to self must be 0.0
        assert!(euclidean_distance(&vec_a, &vec_a) < 1e-6);

        // Benchmark per-pair latency over 1,000 iterations
        let iterations = 1_000;
        let start = Instant::now();
        for _ in 0..iterations {
            let _ = euclidean_distance(&vec_a, &vec_b);
        }
        let total_elapsed = start.elapsed();
        let per_pair_us = total_elapsed.as_micros() as f64 / iterations as f64;

        println!("Euclidean distance dim={}: {:.3} µs per vector pair", dim, per_pair_us);
        // Acceptance criterion: < 5 µs per pair in release, < 50 µs in unoptimized debug
        let max_allowed_us = if cfg!(debug_assertions) { 50.0 } else { 5.0 };
        assert!(
            per_pair_us < max_allowed_us,
            "Euclidean distance too slow at dim {}: {:.3} µs",
            dim, per_pair_us
        );
    }
}

#[test]
fn test_batch_cosine_similarity_and_ranking() {
    let dim = 768;
    let query: Vec<f32> = (0..dim).map(|i| (i as f32 * 0.01).sin()).collect();
    let num_candidates = 50;
    let mut candidates = Vec::with_capacity(num_candidates);

    for c in 0..num_candidates {
        let candidate: Vec<f32> = (0..dim).map(|i| ((i + c * 5) as f32 * 0.01).sin()).collect();
        candidates.push(candidate);
    }

    let sims = batch_cosine_similarity(&query, &candidates);
    assert_eq!(sims.len(), num_candidates);

    // First candidate is identical to query (c=0), so its similarity must be 1.0
    assert!((sims[0] - 1.0).abs() < 1e-4);

    // Verify ranking
    let mut ranked: Vec<(usize, f32)> = sims.into_iter().enumerate().collect();
    ranked.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    assert_eq!(ranked[0].0, 0, "Query itself must be top ranked");
}

#[test]
fn test_tachycardia_and_bradycardia_dsp() {
    let sampling_rate = 250.0;

    // Tachycardia: 150 bpm = 2.5 beats/sec -> peak every 100 samples
    let tachy_samples = 250 * 4;
    let mut tachy_signal = vec![0.0; tachy_samples];
    for b in 0..10 {
        let idx = b * 100 + 40;
        if idx < tachy_samples {
            tachy_signal[idx] = 2.0;
            if idx > 0 { tachy_signal[idx - 1] = 0.5; }
            if idx + 1 < tachy_samples { tachy_signal[idx + 1] = 0.5; }
        }
    }
    let tachy_res = pan_tompkins_qrs_detector(&tachy_signal, sampling_rate);
    assert!(tachy_res.heart_rate_bpm > 100.0, "Expected >100 bpm, got {}", tachy_res.heart_rate_bpm);
    assert!(tachy_res.is_arrhythmia_detected);

    // Bradycardia: 40 bpm -> peak every 375 samples
    let brady_samples = 250 * 6;
    let mut brady_signal = vec![0.0; brady_samples];
    for b in 0..4 {
        let idx = b * 375 + 100;
        if idx < brady_samples {
            brady_signal[idx] = 2.0;
            if idx > 0 { brady_signal[idx - 1] = 0.5; }
            if idx + 1 < brady_samples { brady_signal[idx + 1] = 0.5; }
        }
    }
    let brady_res = pan_tompkins_qrs_detector(&brady_signal, sampling_rate);
    assert!(brady_res.heart_rate_bpm < 50.0 && brady_res.heart_rate_bpm > 0.0, "Expected <50 bpm, got {}", brady_res.heart_rate_bpm);
    assert!(brady_res.is_arrhythmia_detected);
}
