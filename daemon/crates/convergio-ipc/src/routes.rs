//! HTTP routes for IPC — agent registry, messaging, channels, SSE, skills.

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::http::StatusCode;
use axum::response::sse::{Event, KeepAlive};
use axum::response::{IntoResponse, Sse};
use axum::routing::{get, post};
use axum::{Json, Router};
use convergio_db::pool::ConnPool;
use serde::Deserialize;
use serde_json::json;
use tokio::sync::Notify;

use crate::sse::EventBus;

/// Shared state for IPC routes.
#[derive(Clone)]
pub struct IpcState {
    pub pool: ConnPool,
    pub notify: Arc<Notify>,
    pub event_bus: Arc<EventBus>,
    pub rate_limit: u32,
}

/// Build all IPC routes.
pub fn ipc_routes(state: IpcState) -> Router {
    Router::new()
        .route("/api/ipc/agents", get(list_agents))
        .route("/api/ipc/agents/register", post(register_agent))
        .route("/api/ipc/agents/unregister", post(unregister_agent))
        .route("/api/ipc/agents/heartbeat", post(agent_heartbeat))
        .route("/api/ipc/send", post(send_message))
        .route("/api/ipc/messages", get(receive_messages))
        .route("/api/ipc/channels", get(list_channels))
        .route("/api/ipc/skills", get(get_skill_pool))
        .route("/api/ipc/budget", get(get_budget_status))
        .route("/api/ipc/locks", get(list_locks))
        .route("/api/ipc/models", get(list_models))
        .route("/api/ipc/status", get(ipc_status))
        .route("/api/ipc/stream", get(sse_stream))
        .route("/api/events/stream", get(sse_stream))
        .with_state(state)
}

async fn list_agents(State(st): State<IpcState>) -> impl IntoResponse {
    let agents = crate::agents::list(&st.pool).map_err(|e| err(e))?;
    ok(json!(agents))
}

#[derive(Deserialize)]
struct RegisterReq {
    name: String,
    agent_type: String,
    #[serde(default)]
    pid: Option<u32>,
    #[serde(default = "default_host")]
    host: String,
    #[serde(default)]
    metadata: Option<String>,
    #[serde(default)]
    parent_agent: Option<String>,
}

fn default_host() -> String {
    "local".into()
}

async fn register_agent(
    State(st): State<IpcState>,
    Json(r): Json<RegisterReq>,
) -> impl IntoResponse {
    crate::agents::register(
        &st.pool,
        &r.name,
        &r.agent_type,
        r.pid,
        &r.host,
        r.metadata.as_deref(),
        r.parent_agent.as_deref(),
    )
    .map_err(|e| err(e))?;
    ok(json!({"registered": r.name}))
}

#[derive(Deserialize)]
struct UnregReq {
    name: String,
    #[serde(default = "default_host")]
    host: String,
}

async fn unregister_agent(
    State(st): State<IpcState>,
    Json(r): Json<UnregReq>,
) -> impl IntoResponse {
    crate::agents::unregister(&st.pool, &r.name, &r.host).map_err(|e| err(e))?;
    ok(json!({"unregistered": r.name}))
}

#[derive(Deserialize)]
struct HeartbeatReq {
    name: String,
    #[serde(default = "default_host")]
    host: String,
}

async fn agent_heartbeat(
    State(st): State<IpcState>,
    Json(r): Json<HeartbeatReq>,
) -> impl IntoResponse {
    crate::agents::heartbeat(&st.pool, &r.name, &r.host).map_err(|e| err(e))?;
    ok(json!({"ok": true}))
}

#[derive(Deserialize)]
struct SendReq {
    from: String,
    to: String,
    content: String,
    #[serde(default = "default_msg_type")]
    msg_type: String,
    #[serde(default)]
    priority: i32,
}

fn default_msg_type() -> String {
    "text".into()
}

async fn send_message(State(st): State<IpcState>, Json(r): Json<SendReq>) -> impl IntoResponse {
    let params = crate::messaging::SendParams {
        from: &r.from,
        to: &r.to,
        content: &r.content,
        msg_type: &r.msg_type,
        priority: r.priority,
        rate_limit: st.rate_limit,
    };
    let id = crate::messaging::send(&st.pool, &st.notify, &params).map_err(|e| err(e))?;
    ok(json!({"id": id}))
}

#[derive(Deserialize)]
struct RecvQuery {
    agent: String,
    #[serde(default)]
    from: Option<String>,
    #[serde(default)]
    channel: Option<String>,
    #[serde(default = "default_limit")]
    limit: u32,
}

fn default_limit() -> u32 {
    50
}

async fn receive_messages(
    State(st): State<IpcState>,
    Query(q): Query<RecvQuery>,
) -> impl IntoResponse {
    let msgs = crate::messaging::receive(
        &st.pool,
        &q.agent,
        q.from.as_deref(),
        q.channel.as_deref(),
        q.limit,
        false,
    )
    .map_err(|e| err(e))?;
    ok(json!(msgs))
}

async fn list_channels(State(st): State<IpcState>) -> impl IntoResponse {
    let ch = crate::channels::list_channels(&st.pool).map_err(|e| err(e))?;
    ok(json!(ch))
}

async fn get_skill_pool(State(st): State<IpcState>) -> impl IntoResponse {
    let skills = crate::skills::get_skill_pool(&st.pool).map_err(|e| err(e))?;
    ok(json!(skills))
}

#[derive(Deserialize)]
struct BudgetQuery {
    subscription: String,
}

async fn get_budget_status(
    State(st): State<IpcState>,
    Query(q): Query<BudgetQuery>,
) -> impl IntoResponse {
    let status = crate::budget::get_budget_status(&st.pool, &q.subscription).map_err(|e| err(e))?;
    ok(json!(status))
}

async fn list_locks(State(st): State<IpcState>) -> impl IntoResponse {
    let locks = crate::locks::list_locks(&st.pool).map_err(|e| err(e))?;
    ok(json!(locks))
}

async fn list_models(State(st): State<IpcState>) -> impl IntoResponse {
    let models = crate::models::get_all_models(&st.pool).map_err(|e| err(e))?;
    ok(json!(models))
}

async fn ipc_status(State(st): State<IpcState>) -> impl IntoResponse {
    let agents = crate::agents::list(&st.pool).map_err(|e| err(e))?.len();
    let channels = crate::channels::list_channels(&st.pool)
        .map_err(|e| err(e))?
        .len();
    ok(json!({"agents": agents, "channels": channels}))
}

#[derive(Deserialize, Default)]
struct SseFilter {
    #[serde(default)]
    agent: Option<String>,
    #[serde(default)]
    agent_filter: Option<String>,
}

async fn sse_stream(
    State(st): State<IpcState>,
    Query(q): Query<SseFilter>,
) -> Sse<impl futures_core::Stream<Item = Result<Event, std::convert::Infallible>>> {
    let filter = q.agent.or(q.agent_filter);
    let stream = crate::sse::create_sse_stream(st.event_bus, filter);
    Sse::new(stream).keep_alive(KeepAlive::default())
}

fn err(e: impl std::fmt::Display) -> (StatusCode, String) {
    (StatusCode::INTERNAL_SERVER_ERROR, e.to_string())
}

fn ok(v: serde_json::Value) -> Result<Json<serde_json::Value>, (StatusCode, String)> {
    Ok(Json(v))
}
