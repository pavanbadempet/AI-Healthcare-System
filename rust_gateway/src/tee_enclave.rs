#![allow(dead_code)]

use std::collections::HashMap;
use std::sync::Mutex;
use sha2::{Sha256, Digest};
use std::ptr::write_volatile;

use std::sync::LazyLock;

static TRUSTED_MODEL_HASHES: LazyLock<Mutex<HashMap<String, String>>> = LazyLock::new(|| {
    Mutex::new(HashMap::new())
});

pub struct SecureConfidentialEnclave {
    expected_hash: Option<String>,
    attested: bool,
}

impl SecureConfidentialEnclave {
    pub fn new(expected_hash: Option<String>) -> Self {
        Self {
            expected_hash,
            attested: false,
        }
    }

    pub fn attest(&mut self, payload: &[u8]) -> bool {
        let mut hasher = Sha256::new();
        hasher.update(payload);
        let hash_result = format!("{:x}", hasher.finalize());

        if let Some(ref expected) = self.expected_hash {
            if &hash_result != expected {
                return false;
            }
        }

        self.attested = true;
        true
    }

    pub fn attest_model(&mut self, model_name: &str, model_bytes: &[u8]) -> bool {
        let mut hasher = Sha256::new();
        hasher.update(model_bytes);
        let hash_result = format!("{:x}", hasher.finalize());

        let mut hashes = TRUSTED_MODEL_HASHES.lock().unwrap();
        let expected = hashes.entry(model_name.to_string()).or_insert_with(|| hash_result.clone());

        if expected != &hash_result {
            return false;
        }

        self.attested = true;
        true
    }

    pub fn execute<F, R>(&self, mut func: F, mut data: Vec<u8>) -> Result<R, &'static str>
    where
        F: FnMut(&[u8]) -> R,
    {
        if !self.attested {
            return Err("Cannot execute in enclave without successful attestation.");
        }

        let result = func(&data);

        // Compiler-guaranteed secure memory wipe using volatile writes
        // Wipes mutable input buffer data directly in memory so it cannot linger in RAM.
        for byte in data.iter_mut() {
            unsafe {
                write_volatile(byte, 0);
            }
        }
        
        // Deallocate the memory explicitly
        drop(data);

        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_enclave_attestation_and_execution() {
        let expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824".to_string(); // SHA-256 for "hello"
        let mut enclave = SecureConfidentialEnclave::new(Some(expected_hash));
        
        let payload = b"hello";
        assert!(enclave.attest(payload));

        let data = vec![1, 2, 3, 4, 5];
        let exec_res = enclave.execute(|buf| {
            buf.iter().sum::<u8>()
        }, data);

        assert!(exec_res.is_ok());
        assert_eq!(exec_res.unwrap(), 15);
    }
}
