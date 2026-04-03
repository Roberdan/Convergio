//! Settlement — log-only inter-org economics.
//!
//! When Org A delegates to Org B, the cost is recorded as a settlement.
//! For now this is log-only: who owes what to whom. No actual money moves.

use rusqlite::{params, Connection};

use crate::types::SettlementRecord;

/// Record a settlement between two orgs.
pub fn record_settlement(conn: &Connection, record: &SettlementRecord) -> rusqlite::Result<i64> {
    conn.execute(
        "INSERT INTO billing_settlements
         (from_org, to_org, amount_usd, capability, reference_task)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![
            record.from_org,
            record.to_org,
            record.amount_usd,
            record.capability,
            record.reference_task,
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

/// Get settlement balance for an org (positive = owed to them, negative = they owe).
pub fn balance_for_org(conn: &Connection, org_id: &str) -> rusqlite::Result<f64> {
    let received: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(amount_usd), 0.0) FROM billing_settlements
             WHERE to_org = ?1",
            params![org_id],
            |r| r.get(0),
        )
        .unwrap_or(0.0);
    let paid: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(amount_usd), 0.0) FROM billing_settlements
             WHERE from_org = ?1",
            params![org_id],
            |r| r.get(0),
        )
        .unwrap_or(0.0);
    Ok(received - paid)
}

/// List settlements involving an org (as debtor or creditor).
pub fn list_settlements(
    conn: &Connection,
    org_id: &str,
) -> rusqlite::Result<Vec<SettlementRecord>> {
    let mut stmt = conn.prepare(
        "SELECT id, from_org, to_org, amount_usd, capability, reference_task, created_at
         FROM billing_settlements
         WHERE from_org = ?1 OR to_org = ?1
         ORDER BY created_at DESC LIMIT 100",
    )?;
    let rows = stmt.query_map(params![org_id], |row| {
        Ok(SettlementRecord {
            id: row.get(0)?,
            from_org: row.get(1)?,
            to_org: row.get(2)?,
            amount_usd: row.get(3)?,
            capability: row.get(4)?,
            reference_task: row.get(5)?,
            created_at: chrono::Utc::now(),
        })
    })?;
    rows.collect()
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
    fn record_and_balance() {
        let conn = setup();
        record_settlement(
            &conn,
            &SettlementRecord {
                id: None,
                from_org: "acme-corp".into(),
                to_org: "legal-corp".into(),
                amount_usd: 50.0,
                capability: "contract-review".into(),
                reference_task: Some(42),
                created_at: chrono::Utc::now(),
            },
        )
        .unwrap();
        record_settlement(
            &conn,
            &SettlementRecord {
                id: None,
                from_org: "acme-corp".into(),
                to_org: "legal-corp".into(),
                amount_usd: 30.0,
                capability: "contract-review".into(),
                reference_task: Some(43),
                created_at: chrono::Utc::now(),
            },
        )
        .unwrap();

        // legal-corp is owed 80
        let balance = balance_for_org(&conn, "legal-corp").unwrap();
        assert!((balance - 80.0).abs() < 0.001);

        // acme-corp owes 80
        let balance = balance_for_org(&conn, "acme-corp").unwrap();
        assert!((balance - (-80.0)).abs() < 0.001);
    }

    #[test]
    fn list_settlements_includes_both_sides() {
        let conn = setup();
        record_settlement(
            &conn,
            &SettlementRecord {
                id: None,
                from_org: "org-a".into(),
                to_org: "org-b".into(),
                amount_usd: 10.0,
                capability: "search".into(),
                reference_task: None,
                created_at: chrono::Utc::now(),
            },
        )
        .unwrap();
        let list = list_settlements(&conn, "org-a").unwrap();
        assert_eq!(list.len(), 1);
        let list = list_settlements(&conn, "org-b").unwrap();
        assert_eq!(list.len(), 1);
    }
}
