//! Automatic learning extraction — generates key_learnings_json when plan completes.
//!
//! Called from on_plan_done(). Runs as a background tokio task.
//! Collects: task metrics, cost data, respawn counts, evidence gaps, Thor reviews.

use convergio_db::pool::ConnPool;
use rusqlite::params;
use serde_json::json;

/// Extract and persist learnings for a completed plan. Non-blocking.
pub fn extract_plan_learnings(pool: ConnPool, plan_id: i64) {
    tokio::spawn(async move {
        if let Err(e) = do_extract(&pool, plan_id) {
            tracing::warn!(plan_id, error = %e, "learning extraction failed");
        }
    });
}

fn do_extract(pool: &ConnPool, plan_id: i64) -> Result<(), Box<dyn std::error::Error>> {
    let conn = pool.get()?;

    // Skip if learnings already exist
    let existing: Option<String> = conn
        .query_row(
            "SELECT key_learnings_json FROM plan_metadata WHERE plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .ok()
        .flatten();
    if existing.as_deref().is_some_and(|s| !s.is_empty()) {
        tracing::debug!(plan_id, "learnings already exist — skipping");
        return Ok(());
    }

    let metrics = collect_metrics(&conn, plan_id)?;
    let learnings = generate_learnings(&metrics);

    // Persist to plan_metadata
    let json_str = serde_json::to_string(&learnings)?;
    conn.execute(
        "UPDATE plan_metadata SET key_learnings_json = ?1, \
         closed_at = datetime('now') WHERE plan_id = ?2",
        params![json_str, plan_id],
    )?;

    tracing::info!(plan_id, "auto-learnings extracted and stored");
    Ok(())
}

#[derive(Debug)]
struct PlanMetrics {
    tasks_total: i64,
    tasks_done: i64,
    tasks_failed: i64,
    tasks_cancelled: i64,
    waves_total: i64,
    cost_usd: f64,
    total_tokens: i64,
    duration_minutes: Option<f64>,
    agents_used: i64,
    respawn_count: i64,
    tasks_without_evidence: i64,
    pre_review_verdict: Option<String>,
    post_review_verdict: Option<String>,
}

fn collect_metrics(
    conn: &rusqlite::Connection,
    plan_id: i64,
) -> Result<PlanMetrics, Box<dyn std::error::Error>> {
    let tasks_total: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let tasks_done: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 AND status = 'done'",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let tasks_failed: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 AND status = 'failed'",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let tasks_cancelled: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks WHERE plan_id = ?1 AND status = 'cancelled'",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let waves_total: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM waves WHERE plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let cost_usd: f64 = conn
        .query_row(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM token_usage WHERE plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0.0);

    let total_tokens: i64 = conn
        .query_row(
            "SELECT COALESCE(SUM(input_tokens + output_tokens), 0) \
             FROM token_usage WHERE plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Duration: from plan started_at to completed_at
    let duration_minutes: Option<f64> = conn
        .query_row(
            "SELECT (julianday(completed_at) - julianday(started_at)) * 1440.0 \
             FROM plans WHERE id = ?1 AND started_at IS NOT NULL AND completed_at IS NOT NULL",
            params![plan_id],
            |r| r.get(0),
        )
        .ok();

    let agents_used: i64 = conn
        .query_row(
            "SELECT COUNT(DISTINCT a.id) FROM art_agents a \
             JOIN tasks t ON a.task_id = t.id WHERE t.plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let respawn_count: i64 = conn
        .query_row(
            "SELECT COALESCE(SUM(a.respawn_count), 0) FROM art_agents a \
             JOIN tasks t ON a.task_id = t.id WHERE t.plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let tasks_without_evidence: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM tasks t WHERE t.plan_id = ?1 \
             AND t.status IN ('done', 'submitted') \
             AND NOT EXISTS (SELECT 1 FROM task_evidence e WHERE e.task_db_id = t.id)",
            params![plan_id],
            |r| r.get(0),
        )
        .unwrap_or(0);

    // Thor reviews from report_json
    let report_json: Option<String> = conn
        .query_row(
            "SELECT report_json FROM plan_metadata WHERE plan_id = ?1",
            params![plan_id],
            |r| r.get(0),
        )
        .ok()
        .flatten();

    let (pre_review_verdict, post_review_verdict) = parse_review_verdicts(&report_json);

    Ok(PlanMetrics {
        tasks_total,
        tasks_done,
        tasks_failed,
        tasks_cancelled,
        waves_total,
        cost_usd,
        total_tokens,
        duration_minutes,
        agents_used,
        respawn_count,
        tasks_without_evidence,
        pre_review_verdict,
        post_review_verdict,
    })
}

fn parse_review_verdicts(report_json: &Option<String>) -> (Option<String>, Option<String>) {
    let Some(json_str) = report_json else {
        return (None, None);
    };
    let Ok(val) = serde_json::from_str::<serde_json::Value>(json_str) else {
        return (None, None);
    };
    let verdict = val
        .get("verdict")
        .and_then(|v| v.as_str())
        .map(String::from);
    let review_type = val.get("type").and_then(|v| v.as_str()).unwrap_or("");
    match review_type {
        "pre_review" => (verdict, None),
        "post_review" => (None, verdict),
        _ => (verdict.clone(), verdict),
    }
}

fn generate_learnings(m: &PlanMetrics) -> serde_json::Value {
    let mut insights: Vec<String> = Vec::new();

    // Completion rate
    let completion_pct = if m.tasks_total > 0 {
        (m.tasks_done as f64 / m.tasks_total as f64 * 100.0).round()
    } else {
        0.0
    };
    insights.push(format!(
        "Completion: {}/{} tasks done ({completion_pct}%)",
        m.tasks_done, m.tasks_total
    ));

    // Failures
    if m.tasks_failed > 0 {
        insights.push(format!(
            "Warning: {} task(s) failed — investigate root cause",
            m.tasks_failed
        ));
    }

    // Cancellations
    if m.tasks_cancelled > 0 {
        insights.push(format!("{} task(s) cancelled", m.tasks_cancelled));
    }

    // Context exhaustion / respawns
    if m.respawn_count > 0 {
        insights.push(format!(
            "{} respawn(s) — agents hit context limit. Consider splitting tasks",
            m.respawn_count
        ));
    }

    // Evidence gaps
    if m.tasks_without_evidence > 0 {
        insights.push(format!(
            "{} task(s) completed without evidence — enforcement gap",
            m.tasks_without_evidence
        ));
    }

    // Cost efficiency
    if m.tasks_done > 0 && m.cost_usd > 0.0 {
        let cost_per_task = m.cost_usd / m.tasks_done as f64;
        insights.push(format!(
            "Cost: ${:.2} total, ${:.2}/task",
            m.cost_usd, cost_per_task
        ));
    }

    // Duration
    if let Some(mins) = m.duration_minutes {
        if mins > 0.0 {
            let hours = mins / 60.0;
            insights.push(format!("Duration: {hours:.1}h"));
        }
    }

    json!({
        "auto_generated": true,
        "metrics": {
            "tasks_total": m.tasks_total,
            "tasks_done": m.tasks_done,
            "tasks_failed": m.tasks_failed,
            "tasks_cancelled": m.tasks_cancelled,
            "waves_total": m.waves_total,
            "cost_usd": m.cost_usd,
            "total_tokens": m.total_tokens,
            "duration_minutes": m.duration_minutes,
            "agents_used": m.agents_used,
            "respawn_count": m.respawn_count,
            "tasks_without_evidence": m.tasks_without_evidence,
            "completion_pct": completion_pct,
        },
        "reviews": {
            "pre_review": m.pre_review_verdict,
            "post_review": m.post_review_verdict,
        },
        "insights": insights,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn generate_learnings_all_done() {
        let m = PlanMetrics {
            tasks_total: 5,
            tasks_done: 5,
            tasks_failed: 0,
            tasks_cancelled: 0,
            waves_total: 2,
            cost_usd: 1.50,
            total_tokens: 50000,
            duration_minutes: Some(30.0),
            agents_used: 3,
            respawn_count: 0,
            tasks_without_evidence: 0,
            pre_review_verdict: Some("pass".into()),
            post_review_verdict: Some("pass".into()),
        };
        let result = generate_learnings(&m);
        let insights = result["insights"].as_array().unwrap();
        assert!(insights.iter().any(|i| i.as_str().unwrap().contains("5/5")));
        assert!(insights
            .iter()
            .any(|i| i.as_str().unwrap().contains("$1.50")));
        assert!(!insights
            .iter()
            .any(|i| i.as_str().unwrap().contains("failed")));
    }

    #[test]
    fn generate_learnings_with_failures() {
        let m = PlanMetrics {
            tasks_total: 10,
            tasks_done: 7,
            tasks_failed: 2,
            tasks_cancelled: 1,
            waves_total: 3,
            cost_usd: 5.0,
            total_tokens: 100000,
            duration_minutes: Some(120.0),
            agents_used: 5,
            respawn_count: 3,
            tasks_without_evidence: 1,
            pre_review_verdict: Some("pass".into()),
            post_review_verdict: Some("fail".into()),
        };
        let result = generate_learnings(&m);
        let insights = result["insights"].as_array().unwrap();
        assert!(insights
            .iter()
            .any(|i| i.as_str().unwrap().contains("failed")));
        assert!(insights
            .iter()
            .any(|i| i.as_str().unwrap().contains("respawn")));
        assert!(insights
            .iter()
            .any(|i| i.as_str().unwrap().contains("evidence")));
    }

    #[test]
    fn parse_review_verdicts_pre_review() {
        let json = Some(r#"{"type":"pre_review","verdict":"pass"}"#.to_string());
        let (pre, post) = parse_review_verdicts(&json);
        assert_eq!(pre, Some("pass".into()));
        assert_eq!(post, None);
    }

    #[test]
    fn parse_review_verdicts_none() {
        let (pre, post) = parse_review_verdicts(&None);
        assert_eq!(pre, None);
        assert_eq!(post, None);
    }
}
