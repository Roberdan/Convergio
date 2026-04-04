//! HTTP API routes for IPC.
//!
//! - GET  /api/ipc/status   — IPC stats (agents, messages, channels)
//! - GET  /api/ipc/agents   — registered agents list
//! - GET  /api/ipc/channels — channel list
//! - GET  /api/ipc/context  — shared context entries
//! - GET  /api/ipc/messages — message history (query: agent, channel, limit)
//! - GET  /api/ipc/stream   — SSE event stream (query: agent filter)
//! - GET  /api/events/stream — SSE event stream (legacy path)
//! - POST /api/ipc/send     — send a direct message

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::sse::{self, Sse};
use axum::response::Json;
use axum::routing::{get, post};
use axum::Router;
use serde::Deserialize;
use tokio::sync::Notify;

use convergio_db::pool::ConnPool;

use crate::sse::{create_sse_stream, EventBus};

pub struct IpcState {
    pub pool: ConnPool,
    pub notify: Arc<Notify>,
    pub event_bus: Arc<EventBus>,
    pub rate_limit: u32,
}

pub fn ipc_routes(state: Arc<IpcState>) -> Router {
    let bus = Arc::clone(&state.event_bus);
    Router::new()
        .route("/api/ipc/status", get(handle_status))
        .route("/api/ipc/agents", get(handle_agents))
        .route("/api/ipc/channels", get(handle_channels))
        .route("/api/ipc/context", get(handle_context))
        .route("/api/ipc/messages", get(handle_messages))
        .route("/api/ipc/stream", get(handle_stream))
        .route("/api/ipc/send", post(handle_send))
        .with_state(state)
        .merge(event_routes(bus))
}

/// Legacy SSE stream at /api/events/stream (from main branch).
pub fn event_routes(bus: Arc<EventBus>) -> Router {
    Router::new()
        .route("/api/events/stream", get(legacy_stream_handler))
        .with_state(bus)
}

#[derive(serde::Deserialize, Default)]
pub struct LegacyStreamQuery {
    agent_filter: Option<String>,
}

async fn legacy_stream_handler(
    State(bus): State<Arc<EventBus>>,
    Query(q): Query<LegacyStreamQuery>,
) -> Sse<impl futures_core::Stream<Item = Result<sse::Event, std::convert::Infallible>>> {
    Sse::new(create_sse_stream(bus, q.agent_filter)).keep_alive(sse::KeepAlive::default())
}

async fn handle_status(State(state): State<Arc<IpcState>>) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => return Json(serde_json::json!({"error": e.to_string()})),
    };
    let agents: u64 = conn
        .query_row("SELECT count(*) FROM ipc_agents", [], |r| r.get(0))
        .unwrap_or(0);
    let messages: u64 = conn
        .query_row("SELECT count(*) FROM ipc_messages", [], |r| r.get(0))
        .unwrap_or(0);
    let channels: u64 = conn
        .query_row("SELECT count(*) FROM ipc_channels", [], |r| r.get(0))
        .unwrap_or(0);
    Json(serde_json::json!({
        "agents": agents,
        "messages": messages,
        "channels": channels,
    }))
}

async fn handle_agents(State(state): State<Arc<IpcState>>) -> Json<serde_json::Value> {
    match crate::agents::list(&state.pool) {
        Ok(agents) => Json(serde_json::json!(agents)),
        Err(e) => Json(serde_json::json!({"error": e.to_string()})),
    }
}

async fn handle_channels(State(state): State<Arc<IpcState>>) -> Json<serde_json::Value> {
    match crate::channels::list_channels(&state.pool) {
        Ok(ch) => Json(serde_json::json!(ch)),
        Err(e) => Json(serde_json::json!({"error": e.to_string()})),
    }
}

async fn handle_context(State(state): State<Arc<IpcState>>) -> Json<serde_json::Value> {
    match crate::channels::context_list(&state.pool) {
        Ok(ctx) => Json(serde_json::json!(ctx)),
        Err(e) => Json(serde_json::json!({"error": e.to_string()})),
    }
}

#[derive(Debug, Deserialize)]
pub struct MessagesQuery {
    pub agent: Option<String>,
    pub channel: Option<String>,
    pub limit: Option<u32>,
}

async fn handle_messages(
    State(state): State<Arc<IpcState>>,
    Query(params): Query<MessagesQuery>,
) -> Json<serde_json::Value> {
    let limit = params.limit.unwrap_or(50).min(200);
    match crate::messaging::history(
        &state.pool,
        params.agent.as_deref(),
        params.channel.as_deref(),
        limit,
        None,
    ) {
        Ok(msgs) => Json(serde_json::json!(msgs)),
        Err(e) => Json(serde_json::json!({"error": e.to_string()})),
    }
}

#[derive(Debug, Deserialize)]
pub struct StreamQuery {
    pub agent: Option<String>,
}

async fn handle_stream(
    State(state): State<Arc<IpcState>>,
    Query(params): Query<StreamQuery>,
) -> Sse<impl futures_core::Stream<Item = Result<sse::Event, std::convert::Infallible>>> {
    Sse::new(create_sse_stream(
        Arc::clone(&state.event_bus),
        params.agent,
    ))
}

#[derive(Debug, Deserialize)]
pub struct SendRequest {
    pub from: String,
    pub to: String,
    pub content: String,
    #[serde(default = "default_msg_type")]
    pub msg_type: String,
    #[serde(default)]
    pub priority: i32,
}

fn default_msg_type() -> String {
    "text".into()
}

async fn handle_send(
    State(state): State<Arc<IpcState>>,
    Json(body): Json<SendRequest>,
) -> Json<serde_json::Value> {
    let params = crate::messaging::SendParams {
        from: &body.from,
        to: &body.to,
        content: &body.content,
        msg_type: &body.msg_type,
        priority: body.priority,
        rate_limit: state.rate_limit,
    };
    match crate::messaging::send(&state.pool, &state.notify, &params) {
        Ok(id) => Json(serde_json::json!({"id": id})),
        Err(e) => Json(serde_json::json!({"error": e.to_string()})),
    }
}
