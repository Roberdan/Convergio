//! Mesh peer authentication via HMAC-SHA256 challenge-response.
//! Pre-shared key loaded from peers.conf `[mesh]` section.

use hmac::{Hmac, Mac};
use sha2::Sha256;
use std::path::Path;

use crate::error::MeshError;

type HmacSha256 = Hmac<Sha256>;
const NONCE_LEN: usize = 32;

/// Generate a random 32-byte nonce for challenge-response.
pub fn generate_nonce() -> Vec<u8> {
    use rand::RngCore;
    let mut nonce = vec![0u8; NONCE_LEN];
    rand::thread_rng().fill_bytes(&mut nonce);
    nonce
}

/// Compute HMAC-SHA256(secret, data) for challenge-response or HTTP auth.
pub fn compute_hmac(secret: &[u8], data: &[u8]) -> Result<Vec<u8>, MeshError> {
    debug_assert!(!secret.is_empty(), "HMAC secret must not be empty");
    debug_assert!(!data.is_empty(), "HMAC data must not be empty");
    let mut mac = HmacSha256::new_from_slice(secret)
        .map_err(|_| MeshError::Auth("invalid HMAC key length".into()))?;
    mac.update(data);
    Ok(mac.finalize().into_bytes().to_vec())
}

/// Verify a peer's HMAC response against expected.
pub fn verify_hmac(
    secret: &[u8],
    data: &[u8],
    response: &[u8],
) -> Result<bool, MeshError> {
    debug_assert!(!secret.is_empty(), "HMAC secret must not be empty");
    debug_assert!(!data.is_empty(), "HMAC data must not be empty");
    let mut mac = HmacSha256::new_from_slice(secret)
        .map_err(|_| MeshError::Auth("invalid HMAC key length".into()))?;
    mac.update(data);
    Ok(mac.verify_slice(response).is_ok())
}

/// Load shared secret from peers.conf `[mesh]` section.
pub fn load_shared_secret(peers_conf: &Path) -> Option<Vec<u8>> {
    let content = match std::fs::read_to_string(peers_conf) {
        Ok(c) => c,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return None,
        Err(e) => {
            tracing::warn!(
                "failed to read peers.conf at {}: {e}",
                peers_conf.display()
            );
            return None;
        }
    };
    let mut in_mesh_section = false;
    for line in content.lines().map(str::trim) {
        if line.eq_ignore_ascii_case("[mesh]") {
            in_mesh_section = true;
            continue;
        }
        if line.starts_with('[') {
            in_mesh_section = false;
            continue;
        }
        if in_mesh_section {
            if let Some((key, value)) = line.split_once('=') {
                if key.trim() == "shared_secret" {
                    let secret = value.trim();
                    if !secret.is_empty() {
                        return Some(secret.as_bytes().to_vec());
                    }
                }
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn hmac_roundtrip() {
        let secret = b"test-shared-secret-123";
        let nonce = generate_nonce();
        let hmac = compute_hmac(secret, &nonce).unwrap();
        assert!(verify_hmac(secret, &nonce, &hmac).unwrap());
    }

    #[test]
    fn hmac_rejects_wrong_secret() {
        let nonce = generate_nonce();
        let hmac = compute_hmac(b"correct", &nonce).unwrap();
        assert!(!verify_hmac(b"wrong", &nonce, &hmac).unwrap());
    }

    #[test]
    fn hmac_rejects_empty_response() {
        let nonce = generate_nonce();
        assert!(!verify_hmac(b"secret", &nonce, &[]).unwrap());
    }

    #[test]
    fn loads_secret_from_conf() {
        let tmp = std::env::temp_dir().join("test_mesh_auth.conf");
        std::fs::write(&tmp, "[mesh]\nshared_secret = my-key-42\n").unwrap();
        let secret = load_shared_secret(&tmp);
        assert_eq!(secret.as_deref(), Some(b"my-key-42".as_slice()));
        std::fs::remove_file(&tmp).ok();
    }

    #[test]
    fn returns_none_without_mesh_section() {
        let tmp = std::env::temp_dir().join("test_mesh_no_section.conf");
        std::fs::write(&tmp, "[peer1]\nip=1.2.3.4\n").unwrap();
        assert!(load_shared_secret(&tmp).is_none());
        std::fs::remove_file(&tmp).ok();
    }

    #[test]
    fn nonce_uniqueness() {
        let n1 = generate_nonce();
        let n2 = generate_nonce();
        assert_ne!(n1, n2);
        assert_eq!(n1.len(), NONCE_LEN);
    }
}
