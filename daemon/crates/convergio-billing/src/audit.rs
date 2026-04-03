//! Tamper-evident audit trail with hash chain.
//!
//! Every billing transaction is logged with a SHA-256 hash that includes
//! the previous entry's hash, creating an immutable chain. Any tampering
//! breaks the chain and is detectable via verify_chain().

use rusqlite::{params, Connection};
use sha2::{Digest, Sha256};

use crate::types::AuditEntry;

/// Append an entry to the audit chain.
pub fn append(
    conn: &Connection,
    event_type: &str,
    entity_id: &str,
    amount_usd: f64,
    details: &str,
) -> rusqlite::Result<AuditEntry> {
    let prev_hash = get_last_hash(conn)?;
    let hash = compute_hash(&prev_hash, event_type, entity_id, amount_usd, details);

    conn.execute(
        "INSERT INTO billing_audit (event_type, entity_id, amount_usd, details, prev_hash, hash)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![event_type, entity_id, amount_usd, details, prev_hash, hash],
    )?;
    let id = conn.last_insert_rowid();

    Ok(AuditEntry {
        id: Some(id),
        event_type: event_type.to_string(),
        entity_id: entity_id.to_string(),
        amount_usd,
        details: details.to_string(),
        prev_hash,
        hash,
        created_at: chrono::Utc::now(),
    })
}

/// Verify the integrity of the audit chain.
/// Returns Ok(count) if chain is valid, Err with the broken entry ID.
pub fn verify_chain(conn: &Connection) -> rusqlite::Result<Result<usize, i64>> {
    let mut stmt = conn.prepare(
        "SELECT id, event_type, entity_id, amount_usd, details, prev_hash, hash
         FROM billing_audit ORDER BY id ASC",
    )?;
    let entries: Vec<(i64, String, String, f64, String, String, String)> = stmt
        .query_map([], |row| {
            Ok((
                row.get(0)?,
                row.get(1)?,
                row.get(2)?,
                row.get(3)?,
                row.get(4)?,
                row.get(5)?,
                row.get(6)?,
            ))
        })?
        .filter_map(|r| r.ok())
        .collect();

    let mut expected_prev = String::new();
    for (id, event_type, entity_id, amount, details, prev_hash, hash) in &entries {
        if prev_hash != &expected_prev {
            return Ok(Err(*id));
        }
        let computed = compute_hash(prev_hash, event_type, entity_id, *amount, details);
        if &computed != hash {
            return Ok(Err(*id));
        }
        expected_prev = hash.clone();
    }
    Ok(Ok(entries.len()))
}

fn get_last_hash(conn: &Connection) -> rusqlite::Result<String> {
    conn.query_row(
        "SELECT hash FROM billing_audit ORDER BY id DESC LIMIT 1",
        [],
        |r| r.get(0),
    )
    .or(Ok(String::new()))
}

fn compute_hash(
    prev_hash: &str,
    event_type: &str,
    entity_id: &str,
    amount: f64,
    details: &str,
) -> String {
    let mut hasher = Sha256::new();
    hasher.update(prev_hash.as_bytes());
    hasher.update(event_type.as_bytes());
    hasher.update(entity_id.as_bytes());
    hasher.update(amount.to_le_bytes());
    hasher.update(details.as_bytes());
    format!("{:x}", hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::schema::migrations;

    fn setup() -> rusqlite::Connection {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn append_creates_chain() {
        let conn = setup();
        let e1 = append(&conn, "usage", "acme-corp", 10.0, "api calls").unwrap();
        assert!(e1.prev_hash.is_empty());
        assert!(!e1.hash.is_empty());

        let e2 = append(&conn, "usage", "acme-corp", 5.0, "tokens").unwrap();
        assert_eq!(e2.prev_hash, e1.hash);
    }

    #[test]
    fn chain_verification_passes() {
        let conn = setup();
        append(&conn, "usage", "org-a", 10.0, "d1").unwrap();
        append(&conn, "invoice", "org-a", 10.0, "d2").unwrap();
        append(&conn, "settlement", "org-b", 5.0, "d3").unwrap();
        let result = verify_chain(&conn).unwrap();
        assert_eq!(result, Ok(3));
    }

    #[test]
    fn tampered_chain_is_detected() {
        let conn = setup();
        append(&conn, "usage", "org-a", 10.0, "d1").unwrap();
        append(&conn, "usage", "org-a", 5.0, "d2").unwrap();

        // Tamper with the second entry's hash
        conn.execute(
            "UPDATE billing_audit SET hash = 'tampered' WHERE id = 2",
            [],
        )
        .unwrap();

        let result = verify_chain(&conn).unwrap();
        assert!(result.is_err());
    }
}
