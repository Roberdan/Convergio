//! Member and orgchart handlers for convergio-org routes.

use axum::response::Json;
use convergio_db::pool::ConnPool;
use rusqlite::Connection;
use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Deserialize)]
pub struct AddMemberBody {
    pub agent: String,
    pub role: String,
    #[serde(default)]
    pub department: Option<String>,
}

pub fn add_member(pool: &ConnPool, org_id: &str, body: AddMemberBody) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let id = format!("{}-{}", org_id, body.agent);
    match conn.execute(
        "INSERT INTO ipc_org_members (id, org_id, agent, role, department) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        rusqlite::params![id, org_id, body.agent, body.role, body.department],
    ) {
        Ok(_) => Json(json!({"ok": true, "id": id})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

pub fn remove_member(pool: &ConnPool, org_id: &str, agent: &str) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "DELETE FROM ipc_org_members WHERE org_id = ?1 AND agent = ?2",
        rusqlite::params![org_id, agent],
    ) {
        Ok(n) if n > 0 => Json(json!({"ok": true, "removed": n})),
        Ok(_) => Json(json!({"error": "member not found"})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

pub fn load_members(conn: &Connection, org_id: &str) -> Vec<Value> {
    let mut stmt = match conn
        .prepare("SELECT agent, role, department, joined_at FROM ipc_org_members WHERE org_id = ?1")
    {
        Ok(s) => s,
        Err(_) => return vec![],
    };
    let result: Vec<Value> = match stmt.query_map([org_id], |r| {
        Ok(json!({
            "agent": r.get::<_, String>(0)?,
            "role": r.get::<_, String>(1)?,
            "department": r.get::<_, Option<String>>(2)?,
            "joined_at": r.get::<_, String>(3)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    result
}

pub fn get_orgchart(pool: &ConnPool, org_id: &str) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    // Load org info + members, build blueprint, render
    let org_name = conn
        .query_row("SELECT id FROM ipc_orgs WHERE id = ?1", [org_id], |r| {
            r.get::<_, String>(0)
        })
        .unwrap_or_else(|_| org_id.to_string());
    let mission = conn
        .query_row(
            "SELECT mission FROM ipc_orgs WHERE id = ?1",
            [org_id],
            |r| r.get::<_, String>(0),
        )
        .unwrap_or_default();
    let members = load_members(&conn, org_id);
    // Group by department
    let mut departments: std::collections::HashMap<String, Vec<String>> =
        std::collections::HashMap::new();
    for m in &members {
        let dept = m["department"]
            .as_str()
            .unwrap_or("General")
            .to_string();
        let agent = m["agent"].as_str().unwrap_or("?").to_string();
        departments.entry(dept).or_default().push(agent);
    }
    let chart_lines: Vec<String> = departments
        .iter()
        .map(|(dept, agents)| format!("  {} — {}", dept, agents.join(", ")))
        .collect();
    let chart = format!(
        "Org: {}\nMission: {}\nMembers: {}\n{}",
        org_name,
        mission,
        members.len(),
        chart_lines.join("\n")
    );
    Json(json!({"orgchart": chart}))
}

#[derive(Deserialize)]
pub struct UpdateOrgBody {
    pub mission: Option<String>,
    pub objectives: Option<String>,
    pub budget: Option<f64>,
    pub status: Option<String>,
}

pub fn update_org(pool: &ConnPool, id: &str, body: UpdateOrgBody) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut sets = Vec::new();
    let mut params: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    if let Some(m) = &body.mission {
        sets.push("mission = ?");
        params.push(Box::new(m.clone()));
    }
    if let Some(o) = &body.objectives {
        sets.push("objectives = ?");
        params.push(Box::new(o.clone()));
    }
    if let Some(b) = body.budget {
        sets.push("budget = ?");
        params.push(Box::new(b));
    }
    if let Some(st) = &body.status {
        sets.push("status = ?");
        params.push(Box::new(st.clone()));
    }
    if sets.is_empty() {
        return Json(json!({"error": "no fields to update"}));
    }
    sets.push("updated_at = strftime('%Y-%m-%dT%H:%M:%f','now')");
    params.push(Box::new(id.to_string()));
    let sql = format!("UPDATE ipc_orgs SET {} WHERE id = ?", sets.join(", "));
    let refs: Vec<&dyn rusqlite::types::ToSql> = params.iter().map(|p| p.as_ref()).collect();
    match conn.execute(&sql, refs.as_slice()) {
        Ok(n) => Json(json!({"ok": true, "updated": n})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}
