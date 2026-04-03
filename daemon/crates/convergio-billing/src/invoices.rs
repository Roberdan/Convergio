//! Invoice generation — periodic summaries per org.
//!
//! Groups usage by category for a date range and produces
//! an invoice with line items and total.

use rusqlite::{params, Connection};

use crate::types::{Invoice, InvoiceItem};

/// Generate an invoice for an org covering a date range.
pub fn generate_invoice(
    conn: &Connection,
    org_id: &str,
    period_start: &str,
    period_end: &str,
) -> rusqlite::Result<Invoice> {
    let items = build_line_items(conn, org_id, period_start, period_end)?;
    let total_usd: f64 = items.iter().map(|i| i.total).sum();

    let items_json = serde_json::to_string(&items).unwrap_or_else(|_| "[]".into());
    conn.execute(
        "INSERT INTO billing_invoices (org_id, period_start, period_end, items_json, total_usd)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![org_id, period_start, period_end, items_json, total_usd],
    )?;
    let id = conn.last_insert_rowid();

    Ok(Invoice {
        id: Some(id),
        org_id: org_id.to_string(),
        period_start: period_start.to_string(),
        period_end: period_end.to_string(),
        items,
        total_usd,
        created_at: chrono::Utc::now(),
    })
}

/// List invoices for an org.
pub fn list_invoices(conn: &Connection, org_id: &str) -> rusqlite::Result<Vec<Invoice>> {
    let mut stmt = conn.prepare(
        "SELECT id, org_id, period_start, period_end, items_json, total_usd, created_at
         FROM billing_invoices WHERE org_id = ?1 ORDER BY created_at DESC LIMIT 50",
    )?;
    let rows = stmt.query_map(params![org_id], |row| {
        let items_str: String = row.get(4)?;
        let items: Vec<InvoiceItem> = serde_json::from_str(&items_str).unwrap_or_default();
        Ok(Invoice {
            id: row.get(0)?,
            org_id: row.get(1)?,
            period_start: row.get(2)?,
            period_end: row.get(3)?,
            items,
            total_usd: row.get(5)?,
            created_at: chrono::Utc::now(),
        })
    })?;
    rows.collect()
}

fn build_line_items(
    conn: &Connection,
    org_id: &str,
    from: &str,
    to: &str,
) -> rusqlite::Result<Vec<InvoiceItem>> {
    let mut stmt = conn.prepare(
        "SELECT category, SUM(quantity), SUM(cost_usd), unit
         FROM billing_usage
         WHERE org_id = ?1 AND date(created_at) BETWEEN ?2 AND ?3
         GROUP BY category, unit ORDER BY SUM(cost_usd) DESC",
    )?;
    let rows = stmt.query_map(params![org_id, from, to], |row| {
        let cat: String = row.get(0)?;
        let qty: f64 = row.get(1)?;
        let total: f64 = row.get(2)?;
        let unit: String = row.get(3)?;
        let unit_price = if qty > 0.0 { total / qty } else { 0.0 };
        Ok(InvoiceItem {
            category: cat.clone(),
            quantity: qty,
            unit_price,
            total,
            description: format!("{cat} ({qty:.0} {unit})"),
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
    fn generate_and_list_invoice() {
        let conn = setup();
        // Insert usage data
        conn.execute(
            "INSERT INTO billing_usage (org_id, category, quantity, unit, cost_usd)
             VALUES ('acme-corp', 'token_inference', 5000.0, 'tokens', 15.0)",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO billing_usage (org_id, category, quantity, unit, cost_usd)
             VALUES ('acme-corp', 'api_call', 100.0, 'calls', 5.0)",
            [],
        )
        .unwrap();

        let inv = generate_invoice(&conn, "acme-corp", "2020-01-01", "2030-12-31").unwrap();
        assert_eq!(inv.items.len(), 2);
        assert!((inv.total_usd - 20.0).abs() < 0.001);

        let invoices = list_invoices(&conn, "acme-corp").unwrap();
        assert_eq!(invoices.len(), 1);
        assert_eq!(invoices[0].total_usd, 20.0);
    }

    #[test]
    fn empty_invoice_for_no_usage() {
        let conn = setup();
        let inv = generate_invoice(&conn, "empty-org", "2020-01-01", "2030-12-31").unwrap();
        assert!(inv.items.is_empty());
        assert_eq!(inv.total_usd, 0.0);
    }
}
