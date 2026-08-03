/// Pure Rust High-Speed Auth & Password Hash Processor.
/// Performs bcrypt password hashing and verification in native compiled C/Rust.

use bcrypt::{hash, verify, DEFAULT_COST};

#[allow(dead_code)]
pub fn hash_password_rust(password: &str) -> Result<String, String> {
    hash(password, DEFAULT_COST).map_err(|e| e.to_string())
}

#[allow(dead_code)]
pub fn verify_password_rust(password: &str, hashed: &str) -> bool {
    verify(password, hashed).unwrap_or(false)
}
