//! Decision log handlers for convergio-org routes.

use axum::response::Json;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Deserialize)]
pub struct DecisionBody {
    pub decision: String,
    pub reasoning: String,
    pub plan_id: Option<i64>,
    pub task_id: Option<i64>,
    #[serde(default)]
    pub first_principles: Option<String>,
    #[serde(default)]
    pub alternatives_considered: Option<String>,
    #[serde(default)]
    pub agent: Option<String>,
}

pub fn log(pool: &ConnPool, body: DecisionBody) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO decision_log \
         (decision, reasoning, plan_id, task_id, first_principles, \
          alternatives_considered, agent) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        rusqlite::params![
            body.decision,
            body.reasoning,
            body.plan_id,
            body.task_id,
            body.first_principles,
            body.alternatives_considered,
            body.agent,
        ],
    ) {
        Ok(_) => {
            let id = conn.last_insert_rowid();
            Json(json!({"ok": true, "id": id}))
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

pub fn query(pool: &ConnPool, q: crate::routes::DecisionQuery) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let limit = q.limit.unwrap_or(50).min(200);
    let mut conditions = Vec::new();
    let mut params: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    if let Some(pid) = q.plan_id {
        conditions.push("plan_id = ?");
        params.push(Box::new(pid));
    }
    if let Some(tid) = q.task_id {
        conditions.push("task_id = ?");
        params.push(Box::new(tid));
    }
    if let Some(agent) = &q.agent {
        conditions.push("agent = ?");
        params.push(Box::new(agent.clone()));
    }
    let where_clause = if conditions.is_empty() {
        String::new()
    } else {
        format!("WHERE {}", conditions.join(" AND "))
    };
    let sql = format!(
        "SELECT id, plan_id, task_id, decision, reasoning, first_principles, \
         alternatives_considered, outcome, agent, created_at \
         FROM decision_log {} ORDER BY created_at DESC LIMIT {}",
        where_clause, limit
    );
    let param_refs: Vec<&dyn rusqlite::types::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    let mut stmt = match conn.prepare(&sql) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<Value> = match stmt.query_map(param_refs.as_slice(), |r| {
        Ok(json!({
            "id": r.get::<_, i64>(0)?,
            "plan_id": r.get::<_, Option<i64>>(1)?,
            "task_id": r.get::<_, Option<i64>>(2)?,
            "decision": r.get::<_, String>(3)?,
            "reasoning": r.get::<_, String>(4)?,
            "first_principles": r.get::<_, Option<String>>(5)?,
            "alternatives_considered": r.get::<_, Option<String>>(6)?,
            "outcome": r.get::<_, Option<String>>(7)?,
            "agent": r.get::<_, Option<String>>(8)?,
            "created_at": r.get::<_, Option<String>>(9)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!({"decisions": rows}))
}
