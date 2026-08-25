# Milestone 2 Review Report (Reviewer 2) — Longitudinal, Clinical Calculators & ML Module

## 1. Observation

### Build and Test Execution
- Executed `cargo check` in `rust_gateway/`: Finished in 2.39s with 0 errors and 0 warnings.
- Executed `cargo test` in `rust_gateway/`: All 55 tests passed (16 in `lib.rs`, 23 in `main.rs`, 4 in `adversarial_m1_stress_test.rs`, 6 in `db_and_models_test.rs`, 6 in `ml_parity_and_inference_test.rs`).
- Zero Python runtime dependencies: All model inference runs via ONNX Runtime (`ort` 2.0.0-rc.9), static affine scalers, and native Rust algorithms.

### Integrity Assessment
- **Hardcoded test results / expected outputs**: None found. Real tensor operations, static vector scaling, regression slope formulas, and clinical risk equations are executed.
- **Facade implementations**: None found. Real ONNX sessions are loaded and invoked.
- **Shortcuts bypassing task**: None.
- **Attestation**: Integrity checks PASSED with no integrity violations.

### Code Review Findings

#### [Major] Finding 1: Invariant Feature Normalization in `longitudinal.rs` Causes Artificial Risk Inflation
- **Location**: `rust_gateway/src/ml/longitudinal.rs:185-189`
- **Code**:
  ```rust
  let range = maxs[j] - mins[j];
  let normed = if range.abs() < 1e-9 {
      1.0
  } else {
      (latest_row[j] - mins[j]) / range
  };
  normed_latest.push(normed);
  ```
- **Why this is a problem**:
  When a feature value does not vary across visits (e.g. constant `age`, `gender`, `smoking_history`, or `0.0` for absence of symptoms across consecutive visits), `range` is `0.0`. Setting `normed = 1.0` treats constant features as having maximum possible clinical severity ($1.0$) rather than baseline ($0.0$).
  For example, if a healthy patient has 2 identical visits with all zero/normal values, every feature range is $0.0$, so `normed` becomes $1.0$ for all features. The resulting mean risk becomes $1.0$, clamped to $0.95$, classifying a stable/healthy patient as "VERY HIGH" risk.
  In Python reference (`backend/longitudinal_prediction.py:225-227`), `ranges[ranges == 0] = 1.0` resulting in `(seq - mins) / ranges = 0.0`.
- **Suggested Fix**:
  Change `if range.abs() < 1e-9 { 1.0 }` to `if range.abs() < 1e-9 { 0.0 }`.

#### [Minor] Finding 2: Static Probability Fallback for Tree ZipMap Classifiers in `engine.rs`
- **Location**: `rust_gateway/src/ml/engine.rs:153-155, 193-195`
- **Why**: When ONNX model outputs map sequences instead of dense probability tensors, a fallback nominal probability (`0.92`/`0.08` for heart, `0.90`/`0.10` for stroke) is returned.
- **Suggestion**: For future enhancement, ensure tree models are exported with `zipmap=False` so ONNX Runtime produces native probability tensors.

## 2. Logic Chain

1. **Calculators Accuracy**: `calculators.rs` implements eGFR (2021 race-free CKD-EPI), FIB-4 (stratified by age < 65 vs >= 65), Framingham 2008 10-year CVD risk multivariable regression, qSOFA sepsis assessment, CHA2DS2-VASc stroke risk, and MELD score (UNOS 2016). All mathematical formulas have defensive zero/negative/dialysis guardrails and match clinical literature.
2. **Explainability Precision**: `explain.rs` computes 95% conformal prediction intervals, deterministic feature attributions, and rule-based counterfactual recourse with achievable risk targets.
3. **Module Architecture**: `mod.rs` cleanly encapsulates all ML functionality behind `InferenceManager`, properly exported to `lib.rs` and `main.rs`.
4. **Longitudinal Pipeline**: While missing value imputation (forward -> backward -> zero fill), trajectory regression slope calculation, and attention weighting work as designed, the zero-range min-max normalization branch inverts baseline risk for invariant features, requiring a one-line fix.

## 3. Caveats

- CPU-based ONNX execution was evaluated; GPU execution providers (CUDA/TensorRT) were not evaluated as CPU inference is the target deployment architecture for the gateway.

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

The native Rust ML engine is well-architected, fully eliminates Python from the inference path, passes all tests, and contains no integrity violations. However, the zero-range feature normalization bug in `rust_gateway/src/ml/longitudinal.rs` at line 186 must be corrected from `1.0` to `0.0` to prevent severe false-positive risk inflation for stable/invariant longitudinal visit sequences.

## 5. Verification Method

1. Inspect `rust_gateway/src/ml/longitudinal.rs:185-190`.
2. Run test suite:
   ```bash
   cd rust_gateway
   cargo check
   cargo test --test ml_parity_and_inference_test
   cargo test
   ```
3. Invalidation condition: If `predict_longitudinal` is invoked with two identical healthy visits (e.g. all features 0.0), it currently predicts "VERY HIGH" risk (probability 0.95) due to `normed = 1.0` when `range == 0`. It should predict "LOW" risk.
