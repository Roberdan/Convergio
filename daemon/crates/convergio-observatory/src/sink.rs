//! EventBus → timeline persistence sink.
//!
//! Subscribes to the IPC EventBus and persists every domain event
//! to the obs_timeline table. Without this, events only flow to SSE
//! clients and are lost when nobody is listening.

use std::sync::Arc;

use convergio_db::pool::ConnPool;
use convergio_ipc::sse::EventBus;

use crate::timeline::{self, NewEvent};
use crate::types::EventSource;

/// Spawn a background task that subscribes to the EventBus and
/// writes every event to obs_timeline.
pub fn spawn_timeline_sink(pool: ConnPool, bus: Arc<EventBus>) -> tokio::task::JoinHandle<()> {
    let mut rx = bus.subscribe();
    tokio::spawn(async move {
        loop {
            match rx.recv().await {
                Ok(event) => {
                    let source = classify_source(&event.event_type);
                    let conn = match pool.get() {
                        Ok(c) => c,
                        Err(e) => {
                            tracing::warn!("timeline sink: pool error: {e}");
                            continue;
                        }
                    };
                    let new_evt = NewEvent {
                        source: &source,
                        event_type: &event.event_type,
                        actor: &event.from,
                        org_id: None,
                        node_id: None,
                        summary: &event.content,
                        details_json: None,
                    };
                    if let Err(e) = timeline::record_event(&conn, &new_evt) {
                        tracing::warn!(
                            event_type = event.event_type.as_str(),
                            "timeline sink: write failed: {e}"
                        );
                    }
                }
                Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                    tracing::warn!(dropped = n, "timeline sink lagged");
                }
                Err(tokio::sync::broadcast::error::RecvError::Closed) => {
                    tracing::info!("timeline sink: bus closed, stopping");
                    break;
                }
            }
        }
    })
}

fn classify_source(event_type: &str) -> EventSource {
    match event_type {
        t if t.starts_with("plan_") || t.starts_with("task_") => EventSource::Orchestrator,
        t if t.starts_with("agent_") || t.starts_with("delegation_") => EventSource::Agent,
        t if t.starts_with("budget_") => EventSource::Billing,
        t if t.starts_with("health_") => EventSource::System,
        _ => EventSource::System,
    }
}
