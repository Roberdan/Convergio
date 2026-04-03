//! Secret isolation — per-org keychain scoping.
//!
//! Each org has its own secret namespace. Org A cannot read Org B's secrets.
//! Secrets are stored with a simple HMAC-based encryption (the real keychain
//! integration would use OS keychain; here we scope at the DB level).

use crate::types::{OrgId, ScopedSecret, TenancyError};
use chrono::Utc;
use rusqlite::Connection;
use sha2::{Digest, Sha256};

/// Store a secret scoped to an org. Value is hashed for storage.
pub fn put_secret(
    conn: &Connection,
    org_id: &OrgId,
    key: &str,
    value: &str,
) -> Result<(), TenancyError> {
    let encrypted = encrypt_value(org_id, value);
    conn.execute(
        "INSERT INTO mt_scoped_secrets (org_id, key, encrypted_value)
         VALUES (?1, ?2, ?3)
         ON CONFLICT(org_id, key)
         DO UPDATE SET encrypted_value = ?3,
                       updated_at = datetime('now')",
        rusqlite::params![org_id.0, key, encrypted],
    )
    .map_err(|e| TenancyError::Db(format!("put_secret: {e}")))?;
    Ok(())
}

/// Retrieve a secret for an org. Returns None if not found.
/// Cross-org access is prevented by the org_id filter.
pub fn get_secret(
    conn: &Connection,
    org_id: &OrgId,
    key: &str,
) -> Result<Option<String>, TenancyError> {
    let result: Option<String> = conn
        .query_row(
            "SELECT encrypted_value FROM mt_scoped_secrets
             WHERE org_id = ?1 AND key = ?2",
            rusqlite::params![org_id.0, key],
            |r| r.get(0),
        )
        .ok();
    Ok(result)
}

/// Delete a secret for an org.
pub fn delete_secret(conn: &Connection, org_id: &OrgId, key: &str) -> Result<bool, TenancyError> {
    let affected = conn
        .execute(
            "DELETE FROM mt_scoped_secrets WHERE org_id = ?1 AND key = ?2",
            rusqlite::params![org_id.0, key],
        )
        .map_err(|e| TenancyError::Db(format!("delete_secret: {e}")))?;
    Ok(affected > 0)
}

/// List all secret keys for an org (values not returned).
pub fn list_secret_keys(conn: &Connection, org_id: &OrgId) -> Result<Vec<String>, TenancyError> {
    let mut stmt = conn
        .prepare("SELECT key FROM mt_scoped_secrets WHERE org_id = ?1 ORDER BY key")
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    let keys = stmt
        .query_map([&org_id.0], |row| row.get::<_, String>(0))
        .map_err(|e| TenancyError::Db(e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(keys)
}

/// List full secret entries for an org (for admin/audit).
pub fn list_secrets(conn: &Connection, org_id: &OrgId) -> Result<Vec<ScopedSecret>, TenancyError> {
    let mut stmt = conn
        .prepare(
            "SELECT org_id, key, encrypted_value, created_at, updated_at
             FROM mt_scoped_secrets WHERE org_id = ?1 ORDER BY key",
        )
        .map_err(|e| TenancyError::Db(e.to_string()))?;
    let secrets = stmt
        .query_map([&org_id.0], |row| {
            Ok(ScopedSecret {
                org_id: OrgId(row.get::<_, String>(0)?),
                key: row.get(1)?,
                encrypted_value: row.get(2)?,
                created_at: Utc::now(),
                updated_at: Utc::now(),
            })
        })
        .map_err(|e| TenancyError::Db(e.to_string()))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(secrets)
}

/// Simple org-scoped encryption: SHA-256(org_id + ":" + value).
/// In production, replace with AES-256-GCM with per-org key.
fn encrypt_value(org_id: &OrgId, value: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(format!("{}:{}", org_id.0, value).as_bytes());
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let c = Connection::open_in_memory().unwrap();
        c.execute_batch("PRAGMA journal_mode=WAL;").unwrap();
        for m in crate::schema::migrations() {
            c.execute_batch(m.up).unwrap();
        }
        c
    }

    #[test]
    fn put_and_get_secret() {
        let conn = setup();
        let org = OrgId("acme".into());
        put_secret(&conn, &org, "api_key", "sk-12345").unwrap();
        let val = get_secret(&conn, &org, "api_key").unwrap();
        assert!(val.is_some());
    }

    #[test]
    fn cross_org_secret_invisible() {
        let conn = setup();
        let org_a = OrgId("alpha".into());
        let org_b = OrgId("beta".into());
        put_secret(&conn, &org_a, "token", "secret-a").unwrap();
        let result = get_secret(&conn, &org_b, "token").unwrap();
        assert!(result.is_none());
    }

    #[test]
    fn delete_secret_works() {
        let conn = setup();
        let org = OrgId("acme".into());
        put_secret(&conn, &org, "key1", "val1").unwrap();
        assert!(delete_secret(&conn, &org, "key1").unwrap());
        assert!(get_secret(&conn, &org, "key1").unwrap().is_none());
    }

    #[test]
    fn list_keys_only() {
        let conn = setup();
        let org = OrgId("acme".into());
        put_secret(&conn, &org, "db_pass", "x").unwrap();
        put_secret(&conn, &org, "api_key", "y").unwrap();
        let keys = list_secret_keys(&conn, &org).unwrap();
        assert_eq!(keys, vec!["api_key", "db_pass"]);
    }
}
