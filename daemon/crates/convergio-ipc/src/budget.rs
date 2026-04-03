use rusqlite::params;

use crate::types::{AlertLevel, BudgetAlert, BudgetEntry, BudgetStatus, IpcResult};
use convergio_db::pool::ConnPool;

// ── Usage tracking ───────────────────────────────

pub fn log_usage(pool: &ConnPool, entry: &BudgetEntry) -> IpcResult<()> {
    let conn = pool.get()?;
    conn.execute(
        "INSERT INTO ipc_budget_log
         (subscription, date, tokens_in, tokens_out, estimated_cost_usd, model, task_ref)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        params![
            entry.subscription,
            entry.date,
            entry.tokens_in,
            entry.tokens_out,
            entry.estimated_cost_usd,
            entry.model,
            entry.task_ref,
        ],
    )?;
    Ok(())
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct DailySummary {
    pub date: String,
    pub total_tokens_in: i64,
    pub total_tokens_out: i64,
    pub total_cost: f64,
}

pub fn get_daily_summary(pool: &ConnPool, subscription: &str) -> IpcResult<Vec<DailySummary>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT date, SUM(tokens_in), SUM(tokens_out), SUM(estimated_cost_usd)
         FROM ipc_budget_log WHERE subscription = ?1
         GROUP BY date ORDER BY date DESC LIMIT 30",
    )?;
    let rows = stmt
        .query_map(params![subscription], |row| {
            Ok(DailySummary {
                date: row.get(0)?,
                total_tokens_in: row.get(1)?,
                total_tokens_out: row.get(2)?,
                total_cost: row.get(3)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(rows)
}

// ── Budget status ────────────────────────────────

pub fn get_budget_status(pool: &ConnPool, subscription: &str) -> IpcResult<Option<BudgetStatus>> {
    let conn = pool.get()?;
    let sub_row = conn.query_row(
        "SELECT budget_usd, reset_day FROM ipc_subscriptions WHERE name = ?1",
        params![subscription],
        |row| Ok((row.get::<_, f64>(0)?, row.get::<_, i32>(1)?)),
    );
    let (budget_usd, reset_day) = match sub_row {
        Ok(r) => r,
        Err(rusqlite::Error::QueryReturnedNoRows) => return Ok(None),
        Err(e) => return Err(e.into()),
    };
    let total_spent: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(estimated_cost_usd), 0.0)
             FROM ipc_budget_log WHERE subscription = ?1",
            params![subscription],
            |r| r.get(0),
        )
        .unwrap_or(0.0);
    let day_count: i64 = conn
        .query_row(
            "SELECT COUNT(DISTINCT date) FROM ipc_budget_log WHERE subscription = ?1",
            params![subscription],
            |r| r.get(0),
        )
        .unwrap_or(1);
    let daily_avg = if day_count > 0 { total_spent / day_count as f64 } else { 0.0 };
    let days_remaining = (reset_day - 1).max(1);
    Ok(Some(BudgetStatus {
        subscription: subscription.to_string(),
        budget_usd,
        total_spent,
        remaining_budget: budget_usd - total_spent,
        days_remaining,
        daily_avg,
        projected_total: total_spent + daily_avg * days_remaining as f64,
        usage_pct: if budget_usd > 0.0 { (total_spent / budget_usd) * 100.0 } else { 0.0 },
    }))
}

// ── Cost estimation ──────────────────────────────

pub fn estimate_cost(model: &str, tokens_in: i64, tokens_out: i64) -> f64 {
    let (in_rate, out_rate) = match model {
        m if m.contains("opus") => (0.015, 0.075),
        m if m.contains("sonnet") => (0.003, 0.015),
        m if m.contains("haiku") => (0.00025, 0.00125),
        m if m.contains("gpt-4o-mini") => (0.00015, 0.0006),
        m if m.contains("gpt-4o") => (0.005, 0.015),
        _ => (0.003, 0.015),
    };
    (tokens_in as f64 / 1000.0) * in_rate + (tokens_out as f64 / 1000.0) * out_rate
}

// ── Alerts ───────────────────────────────────────

pub fn check_budget_thresholds(
    pool: &ConnPool,
    subscription: &str,
) -> IpcResult<Option<BudgetAlert>> {
    let status = match get_budget_status(pool, subscription)? {
        Some(s) => s,
        None => return Ok(None),
    };
    let pct = status.usage_pct;
    let (level, prefix) = if pct >= 95.0 {
        (AlertLevel::Critical, "CRITICAL")
    } else if pct >= 85.0 {
        (AlertLevel::High, "HIGH")
    } else if pct >= 70.0 {
        (AlertLevel::Warning, "WARNING")
    } else {
        return Ok(None);
    };
    Ok(Some(BudgetAlert {
        subscription: subscription.to_string(),
        level,
        usage_pct: pct,
        message: format!("{prefix}: {subscription} at {pct:.0}%"),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::BudgetEntry;

    fn pool() -> ConnPool {
        let p = convergio_db::pool::create_memory_pool().unwrap();
        let conn = p.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "ipc", &crate::schema::migrations())
            .unwrap();
        p
    }

    fn entry(sub: &str, cost: f64) -> BudgetEntry {
        BudgetEntry {
            subscription: sub.into(),
            date: "2026-04-03".into(),
            tokens_in: 100,
            tokens_out: 100,
            estimated_cost_usd: cost,
            model: "claude-sonnet".into(),
            task_ref: "".into(),
        }
    }

    fn add_subscription(pool: &ConnPool, name: &str, budget: f64) {
        let conn = pool.get().unwrap();
        conn.execute(
            "INSERT INTO ipc_subscriptions VALUES (?1, 'anthropic', 'pro', ?2, 30, '[]')",
            params![name, budget],
        )
        .unwrap();
    }

    #[test]
    fn log_and_summary() {
        let p = pool();
        add_subscription(&p, "s1", 100.0);
        log_usage(&p, &entry("s1", 5.0)).unwrap();
        let summary = get_daily_summary(&p, "s1").unwrap();
        assert_eq!(summary.len(), 1);
        assert!((summary[0].total_cost - 5.0).abs() < 0.001);
    }

    #[test]
    fn alert_at_96_pct() {
        let p = pool();
        add_subscription(&p, "s1", 100.0);
        log_usage(&p, &entry("s1", 96.0)).unwrap();
        let alert = check_budget_thresholds(&p, "s1").unwrap().unwrap();
        assert_eq!(alert.level, AlertLevel::Critical);
    }

    #[test]
    fn no_alert_under_70_pct() {
        let p = pool();
        add_subscription(&p, "s1", 100.0);
        log_usage(&p, &entry("s1", 50.0)).unwrap();
        let alert = check_budget_thresholds(&p, "s1").unwrap();
        assert!(alert.is_none());
    }

    #[test]
    fn cost_estimation() {
        let cost = estimate_cost("claude-opus", 1000, 1000);
        assert!((cost - 0.090).abs() < 0.001);
    }
}
