//! HTTP routes for backup, restore, retention, and org export/import.

use axum::extract::State;
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};
use std::path::PathBuf;
use std::sync::Arc;

/// Shared state for backup routes.
#[derive(Clone)]
pub struct BackupState {
    pub pool: ConnPool,
    pub db_path: PathBuf,
    pub backup_dir: PathBuf,
    pub node_name: String,
}

/// Build the backup router.
pub fn router(state: Arc<BackupState>) -> Router {
    Router::new()
        .route("/api/backup/snapshots", get(list_snapshots))
        .route("/api/backup/snapshots/create", post(create_snapshot))
        .route("/api/backup/snapshots/verify", post(verify_snapshot))
        .route("/api/backup/restore", post(restore_snapshot))
        .route("/api/backup/retention/rules", get(get_retention_rules))
        .route("/api/backup/retention/rules", post(set_retention_rule))
        .route("/api/backup/retention/purge", post(run_purge))
        .route("/api/backup/purge-log", get(get_purge_log))
        .route("/api/backup/export", post(export_org))
        .route("/api/backup/import", post(import_org))
        .with_state(state)
}

async fn list_snapshots(State(st): State<Arc<BackupState>>) -> Json<Value> {
    match crate::snapshot::list_snapshots(&st.pool) {
        Ok(list) => Json(json!({"ok": true, "snapshots": list})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct CreateSnapshotReq {
    /// Optional label for the snapshot (reserved for future use).
    #[serde(default)]
    #[allow(dead_code)]
    label: Option<String>,
}

async fn create_snapshot(
    State(st): State<Arc<BackupState>>,
    Json(_body): Json<CreateSnapshotReq>,
) -> Json<Value> {
    match crate::snapshot::create_snapshot(&st.pool, &st.db_path, &st.backup_dir, &st.node_name) {
        Ok(rec) => Json(json!({"ok": true, "snapshot": rec})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct SnapshotIdReq {
    id: String,
}

async fn verify_snapshot(
    State(st): State<Arc<BackupState>>,
    Json(body): Json<SnapshotIdReq>,
) -> Json<Value> {
    match crate::snapshot::get_snapshot(&st.pool, &body.id) {
        Ok(rec) => match crate::snapshot::verify_snapshot(&rec) {
            Ok(valid) => Json(json!({"ok": true, "valid": valid})),
            Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
        },
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

async fn restore_snapshot(
    State(st): State<Arc<BackupState>>,
    Json(body): Json<SnapshotIdReq>,
) -> Json<Value> {
    match crate::restore::restore_from_snapshot(&st.pool, &body.id, &st.db_path) {
        Ok(path) => Json(json!({"ok": true, "restored_from": path})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

async fn get_retention_rules(State(st): State<Arc<BackupState>>) -> Json<Value> {
    match crate::retention::load_rules(&st.pool) {
        Ok(rules) => Json(json!({"ok": true, "rules": rules})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct SetRuleReq {
    table: String,
    timestamp_column: Option<String>,
    max_age_days: u32,
    org_id: Option<String>,
}

async fn set_retention_rule(
    State(st): State<Arc<BackupState>>,
    Json(body): Json<SetRuleReq>,
) -> Json<Value> {
    let rule = crate::types::RetentionRule {
        table: body.table,
        timestamp_column: body.timestamp_column.unwrap_or("created_at".into()),
        max_age_days: body.max_age_days,
    };
    match crate::retention::save_rule(&st.pool, &rule, body.org_id.as_deref()) {
        Ok(()) => Json(json!({"ok": true, "rule": rule})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

async fn run_purge(State(st): State<Arc<BackupState>>) -> Json<Value> {
    match crate::retention::run_auto_purge(&st.pool) {
        Ok(events) => Json(json!({"ok": true, "events": events})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

async fn get_purge_log(State(st): State<Arc<BackupState>>) -> Json<Value> {
    let conn = match st.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    let mut stmt = match conn.prepare(
        "SELECT table_name, rows_deleted, cutoff_date, executed_at \
         FROM backup_purge_log ORDER BY executed_at DESC LIMIT 100",
    ) {
        Ok(s) => s,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    let rows = match stmt.query_map([], |row: &rusqlite::Row<'_>| {
        Ok(json!({
            "table": row.get::<_, String>(0)?,
            "rows_deleted": row.get::<_, i64>(1)?,
            "cutoff_date": row.get::<_, String>(2)?,
            "executed_at": row.get::<_, String>(3)?,
        }))
    }) {
        Ok(r) => r,
        Err(e) => return Json(json!({"ok": false, "error": e.to_string()})),
    };
    let entries: Vec<Value> = rows.filter_map(|r| r.ok()).collect();
    Json(json!({"ok": true, "log": entries}))
}

#[derive(Deserialize)]
struct ExportReq {
    org_id: String,
    org_name: String,
}

async fn export_org(
    State(st): State<Arc<BackupState>>,
    Json(body): Json<ExportReq>,
) -> Json<Value> {
    let filename = format!("org-export-{}.json", body.org_id);
    let dest = st.backup_dir.join(&filename);
    match crate::export::export_org_data(
        &st.pool,
        &body.org_id,
        &body.org_name,
        &st.node_name,
        &dest,
    ) {
        Ok(meta) => Json(json!({"ok": true, "meta": meta, "path": dest.to_string_lossy()})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct ImportReq {
    path: String,
}

async fn import_org(
    State(st): State<Arc<BackupState>>,
    Json(body): Json<ImportReq>,
) -> Json<Value> {
    let path = PathBuf::from(&body.path);
    match crate::import::import_org_data(&st.pool, &path) {
        Ok(result) => Json(json!({"ok": true, "result": result})),
        Err(e) => Json(json!({"ok": false, "error": e.to_string()})),
    }
}
