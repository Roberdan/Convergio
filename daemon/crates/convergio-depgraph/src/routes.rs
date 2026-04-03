//! HTTP routes for depgraph: graph JSON, capabilities, OpenAPI, removal check.

use axum::extract::Path;
use axum::routing::get;
use axum::{Json, Router};
use convergio_types::manifest::Manifest;
use serde_json::{json, Value};
use std::sync::Arc;

use crate::graph::DepGraph;
use crate::openapi;
use crate::removal;

/// Shared state for depgraph routes — holds all manifests.
#[derive(Clone)]
pub struct DepgraphState {
    manifests: Arc<Vec<Manifest>>,
}

impl DepgraphState {
    pub fn new(manifests: Vec<Manifest>) -> Self {
        Self {
            manifests: Arc::new(manifests),
        }
    }
}

/// Build the depgraph router. All routes are `Router<()>`.
pub fn router(state: DepgraphState) -> Router {
    Router::new()
        .route("/api/depgraph", get(graph_handler))
        .route("/api/depgraph/validate", get(validate_handler))
        .route("/api/capabilities", get(capabilities_handler))
        .route("/api/openapi", get(openapi_handler))
        .route(
            "/api/depgraph/removal-check/{module_id}",
            get(removal_check_handler),
        )
        .layer(axum::Extension(state))
}

async fn graph_handler(axum::Extension(state): axum::Extension<DepgraphState>) -> Json<Value> {
    let graph = DepGraph::from_manifests(&state.manifests);
    Json(json!({
        "ok": true,
        "graph": graph,
    }))
}

async fn validate_handler(axum::Extension(state): axum::Extension<DepgraphState>) -> Json<Value> {
    match DepGraph::validate(&state.manifests) {
        Ok(()) => Json(json!({ "ok": true, "valid": true, "errors": [] })),
        Err(errors) => Json(json!({
            "ok": true,
            "valid": false,
            "errors": errors,
        })),
    }
}

async fn capabilities_handler(
    axum::Extension(state): axum::Extension<DepgraphState>,
) -> Json<Value> {
    let mut caps = Vec::new();
    for m in state.manifests.iter() {
        for cap in &m.provides {
            caps.push(json!({
                "module": &m.id,
                "name": &cap.name,
                "version": &cap.version,
                "description": &cap.description,
            }));
        }
    }
    let tools: Vec<Value> = state
        .manifests
        .iter()
        .flat_map(|m| {
            m.agent_tools.iter().map(move |t| {
                json!({
                    "module": &m.id,
                    "name": &t.name,
                    "description": &t.description,
                })
            })
        })
        .collect();

    Json(json!({
        "ok": true,
        "capabilities": caps,
        "tools": tools,
        "module_count": state.manifests.len(),
        "capability_count": caps.len(),
        "tool_count": tools.len(),
    }))
}

async fn openapi_handler(axum::Extension(state): axum::Extension<DepgraphState>) -> Json<Value> {
    let spec = openapi::generate(&state.manifests);
    Json(spec)
}

async fn removal_check_handler(
    axum::Extension(state): axum::Extension<DepgraphState>,
    Path(module_id): Path<String>,
) -> Json<Value> {
    let result = removal::check_removal(&module_id, &state.manifests);
    Json(json!({
        "ok": true,
        "removal_check": result,
    }))
}
