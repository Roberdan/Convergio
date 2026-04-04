//! HTTP API routes for convergio-org-package.
//!
//! - POST /api/org-packages/install    — install a package
//! - GET  /api/org-packages            — list installed packages
//! - GET  /api/org-packages/:id        — get package details
//! - DELETE /api/org-packages/:id      — uninstall package
//! - POST /api/org-packages/validate   — validate a manifest

use std::sync::Arc;

use axum::extract::{Path, State};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::{json, Value};

pub struct OrgPkgState {
    pub pool: ConnPool,
}

pub fn org_package_routes(state: Arc<OrgPkgState>) -> Router {
    Router::new()
        .route("/api/org-packages/install", post(install_package))
        .route("/api/org-packages/validate", post(validate_manifest))
        .route("/api/org-packages", get(list_packages))
        .route(
            "/api/org-packages/:id",
            get(get_package).delete(uninstall_package),
        )
        .with_state(state)
}

#[derive(Deserialize)]
struct InstallBody {
    /// "local", "github", or "registry"
    source_type: String,
    /// Path, "owner/repo", or registry URL
    source: String,
    /// Raw manifest TOML content (required for local)
    #[serde(default)]
    manifest_toml: Option<String>,
    /// HMAC signing secret (optional)
    #[serde(default)]
    signing_secret: Option<String>,
}

async fn install_package(
    State(s): State<Arc<OrgPkgState>>,
    Json(body): Json<InstallBody>,
) -> Json<Value> {
    // Parse manifest
    let manifest_str = match &body.manifest_toml {
        Some(m) => m.clone(),
        None => return Json(json!({"error": "manifest_toml required for install"})),
    };
    let manifest = match crate::manifest::parse_manifest(&manifest_str) {
        Ok(m) => m,
        Err(e) => return Json(json!({"error": format!("invalid manifest: {e}")})),
    };

    // Check not already installed
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let existing: i64 = conn
        .query_row(
            "SELECT count(*) FROM org_packages WHERE name = ?1 AND version = ?2",
            rusqlite::params![manifest.package.name, manifest.package.version],
            |r| r.get(0),
        )
        .unwrap_or(0);
    if existing > 0 {
        return Json(json!({"error": "package already installed"}));
    }

    // Create sandbox
    let sandbox = crate::sandbox::create_sandbox(&manifest);

    // Sign if secret provided
    let signature = body.signing_secret.as_ref().and_then(|secret| {
        crate::signing::sign_package(manifest_str.as_bytes(), secret.as_bytes()).ok()
    });
    let digest = crate::signing::content_digest(manifest_str.as_bytes());

    // Insert into DB
    let manifest_json = serde_json::to_string(&manifest).unwrap_or_default();
    match conn.execute(
        "INSERT INTO org_packages \
         (name, version, description, author, source, manifest_json, signature, \
          content_digest, db_prefix, route_prefix, ipc_prefix) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
        rusqlite::params![
            manifest.package.name,
            manifest.package.version,
            manifest.package.description,
            manifest.package.author,
            format!("{}:{}", body.source_type, body.source),
            manifest_json,
            signature,
            digest,
            sandbox.db_prefix,
            sandbox.route_prefix,
            sandbox.ipc_prefix,
        ],
    ) {
        Ok(_) => Json(json!({
            "ok": true,
            "name": manifest.package.name,
            "version": manifest.package.version,
            "sandbox": {
                "db_prefix": sandbox.db_prefix,
                "route_prefix": sandbox.route_prefix,
                "ipc_prefix": sandbox.ipc_prefix,
            }
        })),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

async fn list_packages(State(s): State<Arc<OrgPkgState>>) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let mut stmt = match conn.prepare(
        "SELECT id, name, version, author, source, db_prefix, route_prefix, installed_at \
         FROM org_packages ORDER BY installed_at DESC",
    ) {
        Ok(s) => s,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    let rows: Vec<Value> = match stmt.query_map([], |r| {
        Ok(json!({
            "id": r.get::<_, i64>(0)?,
            "name": r.get::<_, String>(1)?,
            "version": r.get::<_, String>(2)?,
            "author": r.get::<_, Option<String>>(3)?,
            "source": r.get::<_, String>(4)?,
            "db_prefix": r.get::<_, String>(5)?,
            "route_prefix": r.get::<_, String>(6)?,
            "installed_at": r.get::<_, Option<String>>(7)?,
        }))
    }) {
        Ok(rows) => rows.filter_map(|r| r.ok()).collect(),
        Err(_) => vec![],
    };
    Json(json!({"packages": rows}))
}

async fn get_package(State(s): State<Arc<OrgPkgState>>, Path(id): Path<i64>) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.query_row(
        "SELECT id, name, version, description, author, source, manifest_json, \
         signature, content_digest, db_prefix, route_prefix, ipc_prefix, installed_at \
         FROM org_packages WHERE id = ?1",
        [id],
        |r| {
            Ok(json!({
                "id": r.get::<_, i64>(0)?,
                "name": r.get::<_, String>(1)?,
                "version": r.get::<_, String>(2)?,
                "description": r.get::<_, Option<String>>(3)?,
                "author": r.get::<_, Option<String>>(4)?,
                "source": r.get::<_, String>(5)?,
                "manifest": r.get::<_, String>(6)?,
                "signature": r.get::<_, Option<String>>(7)?,
                "content_digest": r.get::<_, Option<String>>(8)?,
                "db_prefix": r.get::<_, String>(9)?,
                "route_prefix": r.get::<_, String>(10)?,
                "ipc_prefix": r.get::<_, String>(11)?,
                "installed_at": r.get::<_, Option<String>>(12)?,
            }))
        },
    ) {
        Ok(pkg) => Json(json!({"package": pkg})),
        Err(_) => Json(json!({"error": "package not found"})),
    }
}

async fn uninstall_package(State(s): State<Arc<OrgPkgState>>, Path(id): Path<i64>) -> Json<Value> {
    let conn = match s.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(json!({"error": e.to_string()})),
    };
    match conn.execute("DELETE FROM org_packages WHERE id = ?1", [id]) {
        Ok(n) if n > 0 => Json(json!({"ok": true, "removed": n})),
        Ok(_) => Json(json!({"error": "package not found"})),
        Err(e) => Json(json!({"error": e.to_string()})),
    }
}

#[derive(Deserialize)]
struct ValidateBody {
    manifest_toml: String,
}

async fn validate_manifest(Json(body): Json<ValidateBody>) -> Json<Value> {
    match crate::manifest::parse_manifest(&body.manifest_toml) {
        Ok(m) => Json(json!({
            "valid": true,
            "name": m.package.name,
            "version": m.package.version,
        })),
        Err(e) => Json(json!({"valid": false, "error": format!("{e}")})),
    }
}
