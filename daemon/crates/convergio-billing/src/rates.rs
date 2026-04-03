//! Rate cards — each org declares pricing for its capabilities.
//!
//! When Org A delegates to Org B, the cost is based on B's rate card
//! and charged to A (the delegator).

use rusqlite::{params, Connection};

use crate::types::RateCard;

/// Set or update a rate card for an org's capability.
pub fn set_rate(conn: &Connection, rate: &RateCard) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT OR REPLACE INTO billing_rate_cards
         (org_id, capability, price_per_unit, unit, effective_from)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![
            rate.org_id,
            rate.capability,
            rate.price_per_unit,
            rate.unit,
            rate.effective_from,
        ],
    )?;
    Ok(())
}

/// Get all rate cards for an org.
pub fn get_rates(conn: &Connection, org_id: &str) -> rusqlite::Result<Vec<RateCard>> {
    let mut stmt = conn.prepare(
        "SELECT id, org_id, capability, price_per_unit, unit, effective_from
         FROM billing_rate_cards WHERE org_id = ?1 ORDER BY capability",
    )?;
    let rows = stmt.query_map(params![org_id], |row| {
        Ok(RateCard {
            id: row.get(0)?,
            org_id: row.get(1)?,
            capability: row.get(2)?,
            price_per_unit: row.get(3)?,
            unit: row.get(4)?,
            effective_from: row.get(5)?,
        })
    })?;
    rows.collect()
}

/// Get rate for a specific capability.
pub fn get_rate(
    conn: &Connection,
    org_id: &str,
    capability: &str,
) -> rusqlite::Result<Option<RateCard>> {
    let result = conn.query_row(
        "SELECT id, org_id, capability, price_per_unit, unit, effective_from
         FROM billing_rate_cards WHERE org_id = ?1 AND capability = ?2",
        params![org_id, capability],
        |row| {
            Ok(RateCard {
                id: row.get(0)?,
                org_id: row.get(1)?,
                capability: row.get(2)?,
                price_per_unit: row.get(3)?,
                unit: row.get(4)?,
                effective_from: row.get(5)?,
            })
        },
    );
    match result {
        Ok(r) => Ok(Some(r)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e),
    }
}

/// Calculate cost for an inter-org delegation based on rate cards.
/// Returns the cost in USD, or 0 if no rate card exists.
pub fn calculate_delegation_cost(
    conn: &Connection,
    provider_org: &str,
    capability: &str,
    quantity: f64,
) -> rusqlite::Result<f64> {
    match get_rate(conn, provider_org, capability)? {
        Some(rate) => Ok(rate.price_per_unit * quantity),
        None => Ok(0.0),
    }
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
    fn set_and_get_rate_card() {
        let conn = setup();
        set_rate(
            &conn,
            &RateCard {
                id: None,
                org_id: "legal-corp".into(),
                capability: "contract-review".into(),
                price_per_unit: 5.0,
                unit: "document".into(),
                effective_from: "2026-04-01".into(),
            },
        )
        .unwrap();

        let rates = get_rates(&conn, "legal-corp").unwrap();
        assert_eq!(rates.len(), 1);
        assert_eq!(rates[0].capability, "contract-review");
        assert_eq!(rates[0].price_per_unit, 5.0);
    }

    #[test]
    fn delegation_cost_calculation() {
        let conn = setup();
        set_rate(
            &conn,
            &RateCard {
                id: None,
                org_id: "data-co".into(),
                capability: "analysis".into(),
                price_per_unit: 2.5,
                unit: "request".into(),
                effective_from: "2026-04-01".into(),
            },
        )
        .unwrap();

        let cost = calculate_delegation_cost(&conn, "data-co", "analysis", 10.0).unwrap();
        assert!((cost - 25.0).abs() < 0.001);
    }

    #[test]
    fn missing_rate_returns_zero() {
        let conn = setup();
        let cost = calculate_delegation_cost(&conn, "unknown", "cap", 1.0).unwrap();
        assert_eq!(cost, 0.0);
    }
}
