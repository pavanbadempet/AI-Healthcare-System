use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Nonce,
};
use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};
use rand::RngCore;
use sha2::{Digest, Sha256};
use std::env;
use std::fmt;

#[derive(Debug)]
pub enum CryptoError {
    Base64DecodeError(String),
    CiphertextTooShort,
    DecryptionError(String),
    EncryptionError(String),
    Utf8Error(String),
}

impl fmt::Display for CryptoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CryptoError::Base64DecodeError(msg) => write!(f, "Base64 decode error: {}", msg),
            CryptoError::CiphertextTooShort => write!(f, "Ciphertext is too short to contain nonce"),
            CryptoError::DecryptionError(msg) => write!(f, "Decryption error: {}", msg),
            CryptoError::EncryptionError(msg) => write!(f, "Encryption error: {}", msg),
            CryptoError::Utf8Error(msg) => write!(f, "UTF-8 conversion error: {}", msg),
        }
    }
}

impl std::error::Error for CryptoError {}

#[derive(Clone)]
pub struct EncryptionService {
    key: [u8; 32],
}

impl EncryptionService {
    /// Create a new encryption service by deriving a 32-byte key from the provided secret string.
    pub fn new(secret: &str) -> Self {
        // If the secret is valid 32-byte base64 decoded, use those 32 bytes; otherwise SHA-256 hash it.
        let key_bytes = if let Ok(decoded) = BASE64.decode(secret) {
            if decoded.len() == 32 {
                let mut k = [0u8; 32];
                k.copy_from_slice(&decoded);
                k
            } else {
                let mut hasher = Sha256::new();
                hasher.update(secret.as_bytes());
                hasher.finalize().into()
            }
        } else {
            let mut hasher = Sha256::new();
            hasher.update(secret.as_bytes());
            hasher.finalize().into()
        };

        Self { key: key_bytes }
    }

    /// Load encryption service using `DB_ENCRYPTION_KEY` or fallback to `SECRET_KEY`.
    pub fn from_env() -> Self {
        let secret = env::var("DB_ENCRYPTION_KEY")
            .or_else(|_| env::var("SECRET_KEY"))
            .unwrap_or_else(|_| "healthcare_default_secure_encryption_key_32b!".to_string());
        Self::new(&secret)
    }

    /// Encrypt plaintext to base64 string (12-byte random nonce prepended to ciphertext + tag)
    #[allow(deprecated)]
    pub fn encrypt(&self, plaintext: &str) -> Result<String, CryptoError> {
        let cipher = Aes256Gcm::new_from_slice(&self.key)
            .map_err(|e| CryptoError::EncryptionError(format!("{:?}", e)))?;
        
        let mut nonce_bytes = [0u8; 12];
        rand::thread_rng().fill_bytes(&mut nonce_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);

        let ciphertext = cipher
            .encrypt(nonce, plaintext.as_bytes())
            .map_err(|e| CryptoError::EncryptionError(format!("{:?}", e)))?;

        // Combine nonce (12 bytes) + ciphertext (includes tag)
        let mut combined = Vec::with_capacity(12 + ciphertext.len());
        combined.extend_from_slice(&nonce_bytes);
        combined.extend_from_slice(&ciphertext);

        Ok(BASE64.encode(combined))
    }

    /// Decrypt base64 string to plaintext
    #[allow(deprecated)]
    pub fn decrypt(&self, ciphertext_b64: &str) -> Result<String, CryptoError> {
        let combined = BASE64
            .decode(ciphertext_b64)
            .map_err(|e| CryptoError::Base64DecodeError(e.to_string()))?;

        if combined.len() < 12 {
            return Err(CryptoError::CiphertextTooShort);
        }

        let (nonce_bytes, ciphertext) = combined.split_at(12);
        let nonce = Nonce::from_slice(nonce_bytes);
        let cipher = Aes256Gcm::new_from_slice(&self.key)
            .map_err(|e| CryptoError::DecryptionError(format!("{:?}", e)))?;

        let decrypted_bytes = cipher
            .decrypt(nonce, ciphertext)
            .map_err(|e| CryptoError::DecryptionError(format!("{:?}", e)))?;

        String::from_utf8(decrypted_bytes).map_err(|e| CryptoError::Utf8Error(e.to_string()))
    }

    /// Helper for optional plaintext encryption
    pub fn encrypt_opt(&self, opt: Option<&str>) -> Result<Option<String>, CryptoError> {
        match opt {
            Some(s) => self.encrypt(s).map(Some),
            None => Ok(None),
        }
    }

    /// Helper for optional ciphertext decryption
    pub fn decrypt_opt(&self, opt: Option<&str>) -> Result<Option<String>, CryptoError> {
        match opt {
            Some(s) => self.decrypt(s).map(Some),
            None => Ok(None),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encryption_roundtrip() {
        let crypto = EncryptionService::new("super_secret_testing_key_12345");
        let sample = "patient_ssn_123-45-6789;blood_type=O+;diagnosis=hypertension";
        let encrypted = crypto.encrypt(sample).expect("Encryption failed");
        assert_ne!(sample, encrypted);
        let decrypted = crypto.decrypt(&encrypted).expect("Decryption failed");
        assert_eq!(sample, decrypted);
    }

    #[test]
    fn test_encryption_empty_and_unicode() {
        let crypto = EncryptionService::new("test_key");
        let unicode_text = "Patient: 🏥 Dr. Smith - 500mg Paracetamol. ⚕️ Heart Rate: 72 bpm";
        let enc = crypto.encrypt(unicode_text).expect("Enc unicode");
        let dec = crypto.decrypt(&enc).expect("Dec unicode");
        assert_eq!(unicode_text, dec);

        let empty = "";
        let enc_empty = crypto.encrypt(empty).expect("Enc empty");
        let dec_empty = crypto.decrypt(&enc_empty).expect("Dec empty");
        assert_eq!(empty, dec_empty);
    }

    #[test]
    fn test_invalid_decrypt() {
        let crypto = EncryptionService::new("test_key");
        let res = crypto.decrypt("not-valid-base64!!!");
        assert!(res.is_err());

        let res2 = crypto.decrypt("YWJj"); // short invalid payload
        assert!(res2.is_err());
    }
}
