use std::sync::Arc;
use std::time::Duration;

use tokio::sync::broadcast;

#[derive(Debug, Clone, serde::Serialize)]
pub struct IpcEvent {
    pub from: String,
    pub to: Option<String>,
    pub content: String,
    pub event_type: String,
    pub ts: String,
}

pub struct EventBus {
    tx: broadcast::Sender<IpcEvent>,
}

impl EventBus {
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = broadcast::channel(capacity);
        Self { tx }
    }

    pub fn publish(&self, event: IpcEvent) {
        let _ = self.tx.send(event);
    }

    pub fn subscribe(&self) -> broadcast::Receiver<IpcEvent> {
        self.tx.subscribe()
    }
}

pub fn create_sse_stream(
    bus: Arc<EventBus>,
    agent_filter: Option<String>,
) -> impl futures_core::Stream<Item = Result<axum::response::sse::Event, std::convert::Infallible>>
{
    let rx = bus.subscribe();
    futures_core_stream(rx, agent_filter)
}

fn futures_core_stream(
    mut rx: broadcast::Receiver<IpcEvent>,
    agent_filter: Option<String>,
) -> impl futures_core::Stream<Item = Result<axum::response::sse::Event, std::convert::Infallible>>
{
    async_stream::stream! {
        let mut heartbeat = tokio::time::interval(Duration::from_secs(15));
        loop {
            tokio::select! {
                result = rx.recv() => {
                    match result {
                        Ok(event) => {
                            if let Some(ref filter) = agent_filter {
                                let matches = event.from == *filter
                                    || event.to.as_deref() == Some(filter);
                                if !matches {
                                    continue;
                                }
                            }
                            let data = serde_json::to_string(&event)
                                .unwrap_or_default();
                            yield Ok(axum::response::sse::Event::default()
                                .event("message")
                                .data(data));
                        }
                        Err(broadcast::error::RecvError::Lagged(n)) => {
                            let data = serde_json::json!({
                                "reconnect": true,
                                "reason": "lagged",
                                "dropped": n,
                            });
                            yield Ok(axum::response::sse::Event::default()
                                .event("lag")
                                .data(data.to_string()));
                        }
                        Err(broadcast::error::RecvError::Closed) => break,
                    }
                }
                _ = heartbeat.tick() => {
                    yield Ok(axum::response::sse::Event::default()
                        .event("ping")
                        .data(""));
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn event_bus_publish_subscribe() {
        let bus = EventBus::new(16);
        let mut rx = bus.subscribe();
        bus.publish(IpcEvent {
            from: "elena".into(),
            to: Some("baccio".into()),
            content: "ciao".into(),
            event_type: "direct".into(),
            ts: "2026-04-03T12:00:00".into(),
        });
        let event = rx.try_recv().unwrap();
        assert_eq!(event.from, "elena");
        assert_eq!(event.content, "ciao");
    }
}
