use std::ffi::CStr;
use std::os::raw::c_char;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

mod fhir;
mod tee_enclave;

// Define stub AppState to satisfy fhir module router bindings when compiled as FFI lib
#[derive(Clone)]
pub struct AppState {}

// =====================================================================
// 1. C-FFI / ctypes Direct Loader Exports
// =====================================================================

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

#[pymodule]
fn rust_gateway_ffi(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_fhir_patient_py, m)?)?;
    m.add_function(wrap_pyfunction!(attest_enclave_py, m)?)?;
    Ok(())
}
