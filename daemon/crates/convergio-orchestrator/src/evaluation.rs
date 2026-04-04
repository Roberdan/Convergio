// Evaluation framework for planner and Thor quality measurement.
// WHY: Track outcomes and review accuracy to improve orchestration.
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanEvaluation {
    pub id: i64,
    pub plan_id: i64,
    pub evaluator: String,
    pub tasks_total: i64,
    pub tasks_completed: i64,
    pub tasks_failed: i64,
    pub false_positives: i64,
    pub false_negatives: i64,
    pub precision: f64,
    pub recall: f64,
    pub f1_score: f64,
    pub total_cost_usd: f64,
    pub total_duration_secs: i64,
    pub evaluated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThorAccuracy {
    pub total_reviews: i64,
    pub correct_approvals: i64,
    pub correct_rejections: i64,
    pub false_positives: i64,
    pub false_negatives: i64,
    pub precision: f64,
    pub recall: f64,
    pub f1: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReviewOutcome {
    pub id: i64,
    pub plan_id: i64,
    pub task_id: i64,
    pub thor_decision: String,
    pub actual_outcome: String,
    pub is_correct: bool,
    pub recorded_at: String,
}
/// Record a plan evaluation. Returns the new row id.
pub fn record_evaluation(conn: &Connection, eval: &PlanEvaluation) -> rusqlite::Result<i64> {
    conn.execute(
        "INSERT INTO plan_evaluations \
         (plan_id,evaluator,tasks_total,tasks_completed,tasks_failed,\
         false_positives,false_negatives,precision_score,recall_score,\
         f1_score,total_cost_usd,total_duration_secs) \
         VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12)",
        params![
            eval.plan_id,
            eval.evaluator,
            eval.tasks_total,
            eval.tasks_completed,
            eval.tasks_failed,
            eval.false_positives,
            eval.false_negatives,
            eval.precision,
            eval.recall,
            eval.f1_score,
            eval.total_cost_usd,
            eval.total_duration_secs,
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

/// List evaluations, optionally filtered by plan_id.
pub fn list_evaluations(
    conn: &Connection,
    plan_id: Option<i64>,
    limit: u32,
) -> Vec<PlanEvaluation> {
    let (sql, p): (String, Vec<Box<dyn rusqlite::types::ToSql>>) = match plan_id {
        Some(pid) => (
            format!(
                "SELECT id,plan_id,evaluator,tasks_total,tasks_completed,\
                 tasks_failed,false_positives,false_negatives,precision_score,\
                 recall_score,f1_score,total_cost_usd,total_duration_secs,\
                 evaluated_at FROM plan_evaluations \
                 WHERE plan_id=?1 ORDER BY evaluated_at DESC LIMIT {limit}"
            ),
            vec![Box::new(pid)],
        ),
        None => (
            format!(
                "SELECT id,plan_id,evaluator,tasks_total,tasks_completed,\
                 tasks_failed,false_positives,false_negatives,precision_score,\
                 recall_score,f1_score,total_cost_usd,total_duration_secs,\
                 evaluated_at FROM plan_evaluations \
                 ORDER BY evaluated_at DESC LIMIT {limit}"
            ),
            vec![],
        ),
    };
    let mut stmt = match conn.prepare(&sql) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    let pr: Vec<&dyn rusqlite::types::ToSql> = p.iter().map(|b| b.as_ref()).collect();
    stmt.query_map(pr.as_slice(), |r| Ok(row_to_eval(r)))
        .ok()
        .map(|rows| rows.filter_map(|r| r.ok()).collect())
        .unwrap_or_default()
}

fn row_to_eval(r: &rusqlite::Row) -> PlanEvaluation {
    PlanEvaluation {
        id: r.get(0).unwrap_or(0),
        plan_id: r.get(1).unwrap_or(0),
        evaluator: r.get(2).unwrap_or_default(),
        tasks_total: r.get(3).unwrap_or(0),
        tasks_completed: r.get(4).unwrap_or(0),
        tasks_failed: r.get(5).unwrap_or(0),
        false_positives: r.get(6).unwrap_or(0),
        false_negatives: r.get(7).unwrap_or(0),
        precision: r.get(8).unwrap_or(0.0),
        recall: r.get(9).unwrap_or(0.0),
        f1_score: r.get(10).unwrap_or(0.0),
        total_cost_usd: r.get(11).unwrap_or(0.0),
        total_duration_secs: r.get(12).unwrap_or(0),
        evaluated_at: r.get(13).unwrap_or_default(),
    }
}

/// Compute aggregate Thor accuracy across all review outcomes.
pub fn compute_thor_accuracy(conn: &Connection) -> ThorAccuracy {
    let mut acc = ThorAccuracy {
        total_reviews: 0,
        correct_approvals: 0,
        correct_rejections: 0,
        false_positives: 0,
        false_negatives: 0,
        precision: 0.0,
        recall: 0.0,
        f1: 0.0,
    };
    let sql = "SELECT COUNT(*),\
        SUM(CASE WHEN thor_decision='approved' AND actual_outcome='success' THEN 1 ELSE 0 END),\
        SUM(CASE WHEN thor_decision='rejected' AND actual_outcome='failure' THEN 1 ELSE 0 END),\
        SUM(CASE WHEN thor_decision='approved' AND actual_outcome='failure' THEN 1 ELSE 0 END),\
        SUM(CASE WHEN thor_decision='rejected' AND actual_outcome='success' THEN 1 ELSE 0 END)\
        FROM review_outcomes";
    if let Ok(row) = conn.query_row(sql, [], |r| {
        Ok((
            r.get::<_, i64>(0)?,
            r.get::<_, i64>(1)?,
            r.get::<_, i64>(2)?,
            r.get::<_, i64>(3)?,
            r.get::<_, i64>(4)?,
        ))
    }) {
        acc.total_reviews = row.0;
        acc.correct_approvals = row.1;
        acc.correct_rejections = row.2;
        acc.false_positives = row.3;
        acc.false_negatives = row.4;
        let (tp, fp, fn_) = (row.1 as f64, row.3 as f64, row.4 as f64);
        if tp + fp > 0.0 {
            acc.precision = tp / (tp + fp);
        }
        if tp + fn_ > 0.0 {
            acc.recall = tp / (tp + fn_);
        }
        if acc.precision + acc.recall > 0.0 {
            acc.f1 = 2.0 * acc.precision * acc.recall / (acc.precision + acc.recall);
        }
    }
    acc
}

/// Planner success rate: completed / total across evaluations.
pub fn planner_success_rate(conn: &Connection) -> f64 {
    conn.query_row(
        "SELECT COALESCE(SUM(tasks_completed),0),\
         COALESCE(SUM(tasks_total),0) FROM plan_evaluations",
        [],
        |r| {
            let c: f64 = r.get(0)?;
            let t: f64 = r.get(1)?;
            Ok(if t > 0.0 { c / t } else { 0.0 })
        },
    )
    .unwrap_or(0.0)
}

/// Record a Thor review outcome for accuracy tracking.
pub fn record_review_outcome(
    conn: &Connection,
    plan_id: i64,
    task_id: i64,
    thor_decision: &str,
    actual_outcome: &str,
) -> rusqlite::Result<()> {
    let is_correct = (thor_decision == "approved" && actual_outcome == "success")
        || (thor_decision == "rejected" && actual_outcome == "failure");
    conn.execute(
        "INSERT INTO review_outcomes \
         (plan_id,task_id,thor_decision,actual_outcome,is_correct) \
         VALUES (?1,?2,?3,?4,?5)",
        params![plan_id, task_id, thor_decision, actual_outcome, is_correct],
    )?;
    Ok(())
}

/// List review outcomes, optionally filtered by plan_id.
pub fn list_review_outcomes(conn: &Connection, plan_id: Option<i64>) -> Vec<ReviewOutcome> {
    let (sql, p): (&str, Vec<Box<dyn rusqlite::types::ToSql>>) = match plan_id {
        Some(pid) => (
            "SELECT id,plan_id,task_id,thor_decision,actual_outcome,\
             is_correct,recorded_at FROM review_outcomes \
             WHERE plan_id=?1 ORDER BY recorded_at DESC",
            vec![Box::new(pid)],
        ),
        None => (
            "SELECT id,plan_id,task_id,thor_decision,actual_outcome,\
             is_correct,recorded_at FROM review_outcomes \
             ORDER BY recorded_at DESC",
            vec![],
        ),
    };
    let mut stmt = match conn.prepare(sql) {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    let pr: Vec<&dyn rusqlite::types::ToSql> = p.iter().map(|b| b.as_ref()).collect();
    stmt.query_map(pr.as_slice(), |r| Ok(row_to_outcome(r)))
        .ok()
        .map(|rows| rows.filter_map(|r| r.ok()).collect())
        .unwrap_or_default()
}

fn row_to_outcome(r: &rusqlite::Row) -> ReviewOutcome {
    ReviewOutcome {
        id: r.get(0).unwrap_or(0),
        plan_id: r.get(1).unwrap_or(0),
        task_id: r.get(2).unwrap_or(0),
        thor_decision: r.get(3).unwrap_or_default(),
        actual_outcome: r.get(4).unwrap_or_default(),
        is_correct: r.get::<_, i64>(5).unwrap_or(0) != 0,
        recorded_at: r.get(6).unwrap_or_default(),
    }
}
#[cfg(test)]
#[path = "evaluation_tests.rs"]
mod tests;
