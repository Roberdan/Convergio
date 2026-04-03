//! Minimal JWT (HMAC-SHA256) for agent identity tokens.

use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
use hmac::{Hmac, Mac};
use serde::{Deserialize, Serialize};
use sha2::Sha256;
use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};

type HmacSha256 = Hmac<Sha256>;

static JWT_SECRET: OnceLock<Vec<u8>> = OnceLock::new();

/// Initialise the JWT secret. Call once at daemon startup.
pub fn init_jwt_secret(secret: Option<&[u8]>) {
    let _ = JWT_SECRET.set(match secret {
        Some(s) => s.to_vec(),
        None => match std::env::var("CONVERGIO_JWT_SECRET") {
            Ok(s) if !s.is_empty() => s.into_bytes(),
            _ => {
                let mut buf = [0u8; 32];
                getrandom::getrandom(&mut buf).expect("random fill");
                tracing::warn!("No JWT secret — using ephemeral secret");
                buf.to_vec()
            }
        },
    });
}

fn get_secret() -> &'static [u8] {
    JWT_SECRET.get().map(|v| v.as_slice()).unwrap_or(b"")
}

/// Agent role for RBAC.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AgentRole {
    Coordinator,
    Executor,
    Kernel,
    Worker,
    Dashboard,
}

impl std::fmt::Display for AgentRole {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Coordinator => write!(f, "coordinator"),
            Self::Executor => write!(f, "executor"),
            Self::Kernel => write!(f, "kernel"),
            Self::Worker => write!(f, "worker"),
            Self::Dashboard => write!(f, "dashboard"),
        }
    }
}

/// JWT claims for an agent identity token.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentClaims {
    pub sub: String,
    pub role: AgentRole,
    pub cap: Vec<String>,
    pub iat: u64,
    pub exp: u64,
}

#[derive(Debug, thiserror::Error)]
pub enum JwtError {
    #[error("invalid token format")]
    InvalidFormat,
    #[error("invalid signature")]
    InvalidSignature,
    #[error("token expired")]
    Expired,
    #[error("encoding error: {0}")]
    Encoding(String),
}

/// Issue a signed JWT for an agent.
pub fn issue_token(
    agent_name: &str,
    role: AgentRole,
    capabilities: Vec<String>,
    ttl_secs: u64,
) -> Result<String, JwtError> {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let claims = AgentClaims {
        sub: agent_name.to_string(),
        role,
        cap: capabilities,
        iat: now,
        exp: now + ttl_secs,
    };
    encode(&claims)
}

/// Validate a JWT and return the embedded claims.
pub fn validate_token(token: &str) -> Result<AgentClaims, JwtError> {
    let claims = decode(token)?;
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    if now > claims.exp {
        return Err(JwtError::Expired);
    }
    Ok(claims)
}

fn encode(claims: &AgentClaims) -> Result<String, JwtError> {
    let header = r#"{"alg":"HS256","typ":"JWT"}"#;
    let h = URL_SAFE_NO_PAD.encode(header.as_bytes());
    let payload = serde_json::to_vec(claims).map_err(|e| JwtError::Encoding(e.to_string()))?;
    let p = URL_SAFE_NO_PAD.encode(&payload);
    let signing_input = format!("{h}.{p}");
    let sig = sign(signing_input.as_bytes());
    let s = URL_SAFE_NO_PAD.encode(sig);
    Ok(format!("{signing_input}.{s}"))
}

fn decode(token: &str) -> Result<AgentClaims, JwtError> {
    let parts: Vec<&str> = token.splitn(3, '.').collect();
    if parts.len() != 3 {
        return Err(JwtError::InvalidFormat);
    }
    let signing_input = format!("{}.{}", parts[0], parts[1]);
    let sig = URL_SAFE_NO_PAD
        .decode(parts[2])
        .map_err(|_| JwtError::InvalidFormat)?;
    if !verify(signing_input.as_bytes(), &sig) {
        return Err(JwtError::InvalidSignature);
    }
    let payload = URL_SAFE_NO_PAD
        .decode(parts[1])
        .map_err(|_| JwtError::InvalidFormat)?;
    serde_json::from_slice(&payload).map_err(|_| JwtError::InvalidFormat)
}

fn sign(data: &[u8]) -> Vec<u8> {
    let mut mac = HmacSha256::new_from_slice(get_secret()).expect("HMAC key");
    mac.update(data);
    mac.finalize().into_bytes().to_vec()
}

fn verify(data: &[u8], signature: &[u8]) -> bool {
    let mut mac = HmacSha256::new_from_slice(get_secret()).expect("HMAC key");
    mac.update(data);
    mac.verify_slice(signature).is_ok()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn init_test_secret() {
        let _ = JWT_SECRET.set(b"test-secret-32-bytes-long-enough".to_vec());
    }

    #[test]
    fn issue_and_validate() {
        init_test_secret();
        let token = issue_token("planner", AgentRole::Coordinator, vec![], 3600).unwrap();
        let claims = validate_token(&token).unwrap();
        assert_eq!(claims.sub, "planner");
        assert_eq!(claims.role, AgentRole::Coordinator);
    }

    #[test]
    fn invalid_signature_rejected() {
        init_test_secret();
        let token = issue_token("test", AgentRole::Worker, vec![], 3600).unwrap();
        let tampered = format!("{}X", token);
        assert!(matches!(
            validate_token(&tampered),
            Err(JwtError::InvalidFormat | JwtError::InvalidSignature)
        ));
    }
}
