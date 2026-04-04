// HTTP routes for artifact upload, listing, and download.
// WHY: Non-code projects need file-based evidence (reports, PDFs, screenshots)
// that cannot be represented as git commits.

use std::path::PathBuf;

use axum::body::Body;
use axum::extract::{Multipart, Path, State};
use axum::http::{header, StatusCode};
use axum::response::{IntoResponse, Json};
use axum::routing::{get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde_json::json;
use tokio_util::io::ReaderStream;

use crate::artifacts;

/// Base directory for artifact file storage.
fn artifacts_dir() -> PathBuf {
    PathBuf::from(
        std::env::var("CONVERGIO_ARTIFACTS_DIR")
            .unwrap_or_else(|_| "/tmp/convergio-artifacts".to_string()),
    )
}

pub fn artifact_routes(pool: ConnPool) -> Router {
    Router::new()
        .route("/api/artifacts/upload", post(handle_upload))
        .route("/api/artifacts/plan/:plan_id", get(handle_list_plan))
        .route("/api/artifacts/task/:task_id", get(handle_list_task))
        .route("/api/artifacts/:id", get(handle_get))
        .route("/api/artifacts/:id/download", get(handle_download))
        .with_state(pool)
}

async fn handle_upload(
    State(pool): State<ConnPool>,
    mut multipart: Multipart,
) -> impl IntoResponse {
    let mut task_id: Option<i64> = None;
    let mut plan_id: Option<i64> = None;
    let mut name: Option<String> = None;
    let mut artifact_type = "document".to_string();
    let mut file_data: Option<Vec<u8>> = None;
    let mut file_name: Option<String> = None;

    while let Ok(Some(field)) = multipart.next_field().await {
        let field_name = field.name().unwrap_or("").to_string();
        match field_name.as_str() {
            "task_id" => {
                let text = field.text().await.unwrap_or_default();
                task_id = text.parse().ok();
            }
            "plan_id" => {
                let text = field.text().await.unwrap_or_default();
                plan_id = text.parse().ok();
            }
            "name" => name = Some(field.text().await.unwrap_or_default()),
            "artifact_type" => {
                artifact_type = field.text().await.unwrap_or_default();
            }
            "file" => {
                file_name = field.file_name().map(|s| s.to_string());
                file_data = field.bytes().await.ok().map(|b| b.to_vec());
            }
            _ => {}
        }
    }

    let (Some(task_id), Some(plan_id), Some(data)) = (task_id, plan_id, file_data) else {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({"error": "missing required fields: task_id, plan_id, file"})),
        );
    };

    let display_name =
        name.unwrap_or_else(|| file_name.clone().unwrap_or_else(|| "unnamed".to_string()));
    let safe_file = file_name.unwrap_or_else(|| display_name.clone());

    // Write file to disk
    let dir = artifacts_dir().join(plan_id.to_string());
    if let Err(e) = tokio::fs::create_dir_all(&dir).await {
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": format!("mkdir failed: {e}")})),
        );
    }
    let file_path = dir.join(&safe_file);
    if let Err(e) = tokio::fs::write(&file_path, &data).await {
        return (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": format!("write failed: {e}")})),
        );
    }

    let relative = format!("{plan_id}/{safe_file}");
    let size = data.len() as i64;

    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"error": e.to_string()})),
            )
        }
    };

    match artifacts::record_artifact(
        &conn,
        task_id,
        plan_id,
        &display_name,
        &artifact_type,
        &relative,
        size,
    ) {
        Ok(id) => {
            // Also record as evidence in task_evidence
            let _ = conn.execute(
                "INSERT INTO task_evidence \
                 (task_db_id, evidence_type, command, output_summary, exit_code) \
                 VALUES (?1, 'artifact', ?2, ?3, 0)",
                rusqlite::params![task_id, display_name, format!("artifact_id={id}")],
            );
            (
                StatusCode::CREATED,
                Json(json!({"id": id, "path": relative})),
            )
        }
        Err(e) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({"error": e.to_string()})),
        ),
    }
}

async fn handle_list_plan(
    State(pool): State<ConnPool>,
    Path(plan_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let arts = artifacts::list_artifacts(&conn, plan_id);
    Json(json!(arts))
}

async fn handle_list_task(
    State(pool): State<ConnPool>,
    Path(task_id): Path<i64>,
) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let arts = artifacts::list_task_artifacts(&conn, task_id);
    Json(json!(arts))
}

async fn handle_get(State(pool): State<ConnPool>, Path(id): Path<i64>) -> Json<serde_json::Value> {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match artifacts::get_artifact(&conn, id) {
        Some(art) => Json(json!(art)),
        None => Json(json!({"error": "artifact not found"})),
    }
}

async fn handle_download(State(pool): State<ConnPool>, Path(id): Path<i64>) -> impl IntoResponse {
    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            return (
                StatusCode::INTERNAL_SERVER_ERROR,
                [(header::CONTENT_TYPE, "application/json".to_string())],
                Body::from(json!({"error": e.to_string()}).to_string()),
            )
        }
    };
    let art = match artifacts::get_artifact(&conn, id) {
        Some(a) => a,
        None => {
            return (
                StatusCode::NOT_FOUND,
                [(header::CONTENT_TYPE, "application/json".to_string())],
                Body::from(json!({"error": "not found"}).to_string()),
            )
        }
    };
    drop(conn);

    let file_path = artifacts_dir().join(&art.path);
    let file = match tokio::fs::File::open(&file_path).await {
        Ok(f) => f,
        Err(e) => {
            return (
                StatusCode::NOT_FOUND,
                [(header::CONTENT_TYPE, "application/json".to_string())],
                Body::from(json!({"error": format!("file: {e}")}).to_string()),
            )
        }
    };

    let stream = ReaderStream::new(file);
    let body = Body::from_stream(stream);
    (
        StatusCode::OK,
        [(header::CONTENT_TYPE, "application/octet-stream".to_string())],
        body,
    )
}
