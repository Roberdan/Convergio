//! Notification handlers for convergio-org routes.

use axum::response::Json;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

use crate::telegram::{format_notification, TelegramClient};

#[derive(Deserialize)]
pub struct NotifyBody {
    #[serde(default = "default_severity")]
    pub severity: String,
    pub title: String,
    #[serde(default)]
    pub message: String,
    pub plan_id: Option<i64>,
    pub link: Option<String>,
}

fn default_severity() -> String {
    "info".into()
}

pub fn queue(pool: &ConnPool, body: NotifyBody) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute(
        "INSERT INTO notification_queue (severity, title, message, plan_id, link) \
         VALUES (?1, ?2, ?3, ?4, ?5)",
        rusqlite::params![
            body.severity,
            body.title,
            body.message,
            body.plan_id,
            body.link
        ],
    ) {
        Ok(_) => {
            let id = conn.last_insert_rowid();
            Json(json!({"ok": true, "id": id}))
        }
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

pub fn list_pending(pool: &ConnPool) -> Json<Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut stmt = match conn.prepare(
        "SELECT id, severity, title, message, plan_id, link, status, created_at \
         FROM notification_queue WHERE status = 'pending' \
         ORDER BY created_at DESC LIMIT 100",
    ) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<Value> = match stmt.query_map([], |r| {
        Ok(json!({
            "id": r.get::<_, i64>(0)?,
            "severity": r.get::<_, String>(1)?,
            "title": r.get::<_, String>(2)?,
            "message": r.get::<_, Option<String>>(3)?,
            "plan_id": r.get::<_, Option<i64>>(4)?,
            "link": r.get::<_, Option<String>>(5)?,
            "status": r.get::<_, String>(6)?,
            "created_at": r.get::<_, Option<String>>(7)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!({"notifications": rows}))
}

// --- Telegram test ---

#[derive(Deserialize)]
pub struct TelegramTestBody {
    #[serde(default = "default_severity")]
    pub severity: String,
    pub title: String,
    #[serde(default)]
    pub message: String,
}

pub async fn test_telegram(_pool: &ConnPool, body: TelegramTestBody) -> Json<Value> {
    match TelegramClient::from_env() {
        Ok(client) => {
            let text = format_notification(
                &body.severity,
                &body.title,
                if body.message.is_empty() {
                    None
                } else {
                    Some(&body.message)
                },
                None,
            );
            match client.send(&text).await {
                Ok(_) => Json(json!({"ok": true, "message": "Telegram notification sent"})),
                Err(e) => Json(json!({"error": e})),
            }
        }
        Err(e) => Json(json!({"error": e})),
    }
}
