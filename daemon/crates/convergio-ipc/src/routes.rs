//! HTTP routes for IPC — currently just the SSE event stream.

use std::sync::Arc;

use axum::extract::{Query, State};
use axum::response::sse::{self, Sse};
use axum::routing::get;
use axum::Router;

use crate::sse::{create_sse_stream, EventBus};

#[derive(serde::Deserialize, Default)]
pub struct StreamQuery {
    agent_filter: Option<String>,
}

async fn stream_handler(
    State(bus): State<Arc<EventBus>>,
    Query(q): Query<StreamQuery>,
) -> Sse<impl futures_core::Stream<Item = Result<sse::Event, std::convert::Infallible>>> {
    Sse::new(create_sse_stream(bus, q.agent_filter)).keep_alive(sse::KeepAlive::default())
}

pub fn event_routes(bus: Arc<EventBus>) -> Router {
    Router::new()
        .route("/api/events/stream", get(stream_handler))
        .with_state(bus)
}
