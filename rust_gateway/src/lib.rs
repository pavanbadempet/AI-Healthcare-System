use std::ffi::CStr;
use std::os::raw::c_char;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod fhir;
mod tee_enclave;
mod clinical_calculator;
mod phi_redactor;
mod ecg_dsp;
mod dicom_slicer;
mod auth_crypto;
mod billing_audit;
mod federated_aggregator;

// Define stub AppState to satisfy fhir module router bindings when compiled as FFI lib
#[derive(Clone)]
pub struct AppState {}

// =====================================================================
// 1. C-FFI / ctypes Direct Loader Exports
// =====================================================================

#[unsafe(no_mangle)]
pub extern "C" fn calculate_egfr_ffi(serum_creatinine: f64, age: f64, is_female: bool) -> f64 {
    clinical_calculator::calculate_egfr_ckd_epi(serum_creatinine, age, is_female)
}

#[unsafe(no_mangle)]
pub extern "C" fn validate_fhir_patient_ffi(json_ptr: *const c_char) -> bool {
    if json_ptr.is_null() {
        return false;
    }
    unsafe {
        let c_str = CStr::from_ptr(json_ptr);
        match c_str.to_str() {
            Ok(s) => {
                match serde_json::from_str::<serde_json::Value>(s) {
                    Ok(val) => fhir::validate_fhir_resource_sync(&val).valid,
                    Err(_) => false,
                }
            }
            Err(_) => false,
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn attest_enclave_ffi(
    model_name_ptr: *const c_char,
    model_bytes_ptr: *const u8,
    model_bytes_len: usize,
) -> bool {
    if model_name_ptr.is_null() || model_bytes_ptr.is_null() {
        return false;
    }
    unsafe {
        let name_str = match CStr::from_ptr(model_name_ptr).to_str() {
            Ok(s) => s,
            Err(_) => return false,
        };
        let bytes = std::slice::from_raw_parts(model_bytes_ptr, model_bytes_len);
        let mut enclave = tee_enclave::SecureConfidentialEnclave::new(None);
        enclave.attest_model(name_str, bytes)
    }
}

// =====================================================================
// 2. PyO3 Native CPython Extension Module Exports
// =====================================================================

#[pyfunction]
fn aggregate_fedavg_py(gradients: Vec<Vec<f64>>, weights: Vec<f64>) -> PyResult<Vec<f64>> {
    Ok(federated_aggregator::aggregate_fedavg_gradients(&gradients, &weights))
}

#[pyfunction]
fn hash_password_py(password: &str) -> PyResult<String> {
    auth_crypto::hash_password_rust(password).map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
}

#[pyfunction]
fn verify_password_py(password: &str, hashed: &str) -> PyResult<bool> {
    Ok(auth_crypto::verify_password_rust(password, hashed))
}

#[pyfunction]
fn redact_phi_py(text: &str) -> PyResult<String> {
    Ok(phi_redactor::redact_phi_text(text))
}

#[pyfunction]
fn calculate_egfr_py(serum_creatinine: f64, age: f64, is_female: bool) -> PyResult<f64> {
    Ok(clinical_calculator::calculate_egfr_ckd_epi(serum_creatinine, age, is_female))
}

#[pyfunction]
fn validate_fhir_patient_py(json_str: &str) -> PyResult<bool> {
    match serde_json::from_str::<serde_json::Value>(json_str) {
        Ok(val) => Ok(fhir::validate_fhir_resource_sync(&val).valid),
        Err(_) => Ok(false),
    }
}

#[pyfunction]
fn attest_enclave_py(model_name: &str, model_bytes: Vec<u8>) -> PyResult<bool> {
    let mut enclave = tee_enclave::SecureConfidentialEnclave::new(None);
    Ok(enclave.attest_model(model_name, &model_bytes))
}

#[pyfunction]
fn evaluate_sepsis_qsofa_py(respiratory_rate: f64, systolic_bp: f64, gcs_score: f64) -> PyResult<(i32, String)> {
    let mut score = 0;
    if respiratory_rate >= 22.0 { score += 1; }
    if systolic_bp <= 100.0 { score += 1; }
    if gcs_score < 15.0 { score += 1; }

    let risk = if score >= 2 {
        "SEPTIC_SHOCK_WARNING"
    } else if score == 1 {
        "ELEVATED"
    } else {
        "NORMAL"
    };
    Ok((score, risk.to_string()))
}

#[pyfunction]
fn detect_fraud_score_py(amount: f64, cpt_code: &str, is_duplicate: bool) -> PyResult<(f64, String)> {
    let mut score: f64 = 0.0;
    if is_duplicate { score += 0.5; }
    if amount > 10000.0 && cpt_code.contains("CPT-99211") { score += 0.35; }

    let score_final = score.min(1.0f64);

    let risk = if score_final >= 0.7 {
        "CRITICAL"
    } else if score_final >= 0.4 {
        "HIGH"
    } else {
        "LOW"
    };
    Ok((score_final, risk.to_string()))
}

#[pyfunction]
fn calculate_cosine_similarity_py(vec_a: Vec<f64>, vec_b: Vec<f64>) -> PyResult<f64> {
    let dot: f64 = vec_a.iter().zip(vec_b.iter()).map(|(a, b)| a * b).sum();
    let norm_a: f64 = vec_a.iter().map(|a| a * a).sum::<f64>().sqrt();
    let norm_b: f64 = vec_b.iter().map(|b| b * b).sum::<f64>().sqrt();
    let sim = if norm_a > 0.0 && norm_b > 0.0 { dot / (norm_a * norm_b) } else { 0.0 };
    Ok(sim)
}

#[pymodule]
fn rust_gateway_ffi(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(aggregate_fedavg_py, m)?)?;
    m.add_function(wrap_pyfunction!(hash_password_py, m)?)?;
    m.add_function(wrap_pyfunction!(verify_password_py, m)?)?;
    m.add_function(wrap_pyfunction!(redact_phi_py, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_egfr_py, m)?)?;
    m.add_function(wrap_pyfunction!(validate_fhir_patient_py, m)?)?;
    m.add_function(wrap_pyfunction!(attest_enclave_py, m)?)?;
    m.add_function(wrap_pyfunction!(evaluate_sepsis_qsofa_py, m)?)?;
    m.add_function(wrap_pyfunction!(detect_fraud_score_py, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_cosine_similarity_py, m)?)?;
    Ok(())
}
