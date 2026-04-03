//! Tamper-evident audit chain with SHA-256 hash linking.

use crate::types::{AuditEntry, SecurityError};
use sha2::{Digest, Sha256};
use std::sync::Mutex;

/// Cryptographic audit chain for agent actions.
pub struct AuditChain {
    entries: Mutex<Vec<AuditEntry>>,
    next_id: Mutex<u64>,
}

impl AuditChain {
    pub fn new() -> Self {
        Self {
            entries: Mutex::new(Vec::new()),
            next_id: Mutex::new(1),
        }
    }

    /// Record an agent action in the audit chain.
    pub fn record(
        &self,
        agent_id: &str,
        action: &str,
        target: &str,
        params: &str,
    ) -> Result<AuditEntry, SecurityError> {
        let mut entries = self
            .entries
            .lock()
            .map_err(|e| SecurityError::AuditError(format!("lock: {e}")))?;
        let mut id_counter = self
            .next_id
            .lock()
            .map_err(|e| SecurityError::AuditError(format!("lock: {e}")))?;

        let id = *id_counter;
        *id_counter += 1;

        let prev_hash = entries
            .last()
            .map(|e| e.entry_hash.clone())
            .unwrap_or_else(|| "0".repeat(64));

        let params_hash = sha256_hex(params.as_bytes());
        let timestamp = chrono::Utc::now().to_rfc3339();

        let entry_data =
            format!("{id}{agent_id}{action}{target}{timestamp}{params_hash}{prev_hash}");
        let entry_hash = sha256_hex(entry_data.as_bytes());

        let entry = AuditEntry {
            id,
            agent_id: agent_id.to_string(),
            action: action.to_string(),
            target: target.to_string(),
            timestamp,
            params_hash,
            prev_hash,
            entry_hash,
        };

        entries.push(entry.clone());
        Ok(entry)
    }

    /// Verify chain integrity.
    pub fn verify(&self) -> Result<bool, SecurityError> {
        let entries = self
            .entries
            .lock()
            .map_err(|e| SecurityError::AuditError(format!("lock: {e}")))?;
        for i in 1..entries.len() {
            if entries[i].prev_hash != entries[i - 1].entry_hash {
                return Ok(false);
            }
        }
        Ok(true)
    }

    /// Query entries by agent and/or action.
    pub fn query(&self, agent_id: Option<&str>, action: Option<&str>) -> Vec<AuditEntry> {
        let entries = self.entries.lock().unwrap_or_else(|e| e.into_inner());
        entries
            .iter()
            .filter(|e| agent_id.map(|a| e.agent_id == a).unwrap_or(true))
            .filter(|e| action.map(|a| e.action == a).unwrap_or(true))
            .cloned()
            .collect()
    }

    pub fn len(&self) -> usize {
        self.entries.lock().map(|e| e.len()).unwrap_or(0)
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

impl Default for AuditChain {
    fn default() -> Self {
        Self::new()
    }
}

fn sha256_hex(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn record_and_verify() {
        let chain = AuditChain::new();
        chain.record("agent-1", "deploy", "/api/plans", "{}").unwrap();
        chain.record("agent-1", "validate", "/api/tasks/1", "{}").unwrap();
        assert_eq!(chain.len(), 2);
        assert!(chain.verify().unwrap());
    }

    #[test]
    fn query_by_agent() {
        let chain = AuditChain::new();
        chain.record("alice", "read", "/a", "").unwrap();
        chain.record("bob", "write", "/b", "").unwrap();
        let results = chain.query(Some("alice"), None);
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].agent_id, "alice");
    }
}
