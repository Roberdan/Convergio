//! Persistence layer for HTTP extensions — CRUD on http_extensions table.

use crate::types::{BridgeState, HttpExtension, RegisterRequest};
use chrono::Utc;
use convergio_types::manifest::Manifest;
use rusqlite::{params, Connection};

/// Insert a new HTTP extension registration.
pub fn insert_extension(conn: &Connection, req: &RegisterRequest) -> Result<(), String> {
    let manifest_json =
        serde_json::to_string(&req.manifest).map_err(|e| format!("serialize: {e}"))?;
    let now = Utc::now().to_rfc3339();
    conn.execute(
        "INSERT INTO http_extensions \
         (id, manifest_json, base_url, health_endpoint, events_webhook, \
          routes_prefix, state, registered_at) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
        params![
            req.id,
            manifest_json,
            req.base_url,
            req.health_endpoint,
            req.events_webhook,
            req.routes_prefix,
            BridgeState::Registered.as_str(),
            now,
        ],
    )
    .map_err(|e| format!("insert: {e}"))?;
    Ok(())
}

/// List all non-removed extensions.
pub fn list_active(conn: &Connection) -> Result<Vec<HttpExtension>, String> {
    let mut stmt = conn
        .prepare(
            "SELECT id, manifest_json, base_url, health_endpoint, \
             events_webhook, routes_prefix, state, registered_at, \
             last_health_check, consecutive_failures \
             FROM http_extensions WHERE state != 'removed'",
        )
        .map_err(|e| format!("prepare: {e}"))?;
    let rows = stmt
        .query_map([], row_to_extension)
        .map_err(|e| format!("query: {e}"))?;
    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("collect: {e}"))
}

/// Get a single extension by ID.
pub fn get_by_id(conn: &Connection, id: &str) -> Result<Option<HttpExtension>, String> {
    let mut stmt = conn
        .prepare(
            "SELECT id, manifest_json, base_url, health_endpoint, \
             events_webhook, routes_prefix, state, registered_at, \
             last_health_check, consecutive_failures \
             FROM http_extensions WHERE id = ?1",
        )
        .map_err(|e| format!("prepare: {e}"))?;
    let mut rows = stmt
        .query_map(params![id], row_to_extension)
        .map_err(|e| format!("query: {e}"))?;
    match rows.next() {
        Some(Ok(ext)) => Ok(Some(ext)),
        Some(Err(e)) => Err(format!("row: {e}")),
        None => Ok(None),
    }
}

/// Update extension state and health check timestamp.
pub fn update_health(
    conn: &Connection,
    id: &str,
    state: BridgeState,
    failures: u32,
) -> Result<(), String> {
    let now = Utc::now().to_rfc3339();
    conn.execute(
        "UPDATE http_extensions \
         SET state = ?1, last_health_check = ?2, consecutive_failures = ?3 \
         WHERE id = ?4",
        params![state.as_str(), now, failures, id],
    )
    .map_err(|e| format!("update: {e}"))?;
    Ok(())
}

/// Mark an extension as removed.
pub fn remove_extension(conn: &Connection, id: &str) -> Result<bool, String> {
    let affected = conn
        .execute(
            "UPDATE http_extensions SET state = 'removed' WHERE id = ?1",
            params![id],
        )
        .map_err(|e| format!("remove: {e}"))?;
    Ok(affected > 0)
}

fn row_to_extension(row: &rusqlite::Row<'_>) -> rusqlite::Result<HttpExtension> {
    let manifest_json: String = row.get(1)?;
    let manifest: Manifest = serde_json::from_str(&manifest_json).map_err(|e| {
        rusqlite::Error::FromSqlConversionFailure(1, rusqlite::types::Type::Text, Box::new(e))
    })?;
    let state_str: String = row.get(6)?;
    let state = BridgeState::from_str(&state_str).unwrap_or(BridgeState::Registered);
    let last_hc: Option<String> = row.get(8)?;
    Ok(HttpExtension {
        id: row.get(0)?,
        manifest,
        base_url: row.get(2)?,
        health_endpoint: row.get(3)?,
        events_webhook: row.get(4)?,
        routes_prefix: row.get(5)?,
        state,
        registered_at: row.get::<_, String>(7)?.parse().unwrap_or_default(),
        last_health_check: last_hc.and_then(|s| s.parse().ok()),
        consecutive_failures: row.get(9)?,
    })
}

#[cfg(test)]
#[path = "store_tests.rs"]
mod tests;
