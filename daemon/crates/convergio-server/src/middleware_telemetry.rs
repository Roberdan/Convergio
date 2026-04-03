//! Request telemetry: counters, response time histogram, endpoint metrics.

use axum::body::Body;
use axum::http::header::HeaderName;
use axum::http::Request;
use axum::middleware::Next;
use axum::response::Response;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::RwLock;
use std::time::Instant;

pub const REQUEST_ID_HEADER: &str = "x-request-id";

static TOTAL_REQUESTS: AtomicU64 = AtomicU64::new(0);
static TOTAL_ERRORS: AtomicU64 = AtomicU64::new(0);
static ENDPOINT_METRICS: RwLock<Option<HashMap<String, EndpointStats>>> = RwLock::new(None);

const HISTOGRAM_BUCKETS: &[u64] = &[5, 10, 25, 50, 100, 250, 500, 1000, 5000];

#[derive(Debug, Clone)]
pub struct EndpointStats {
    pub count: u64,
    pub errors: u64,
    pub total_ms: u64,
    pub max_ms: u64,
    pub histogram: Vec<u64>,
}

impl EndpointStats {
    fn new() -> Self {
        Self {
            count: 0,
            errors: 0,
            total_ms: 0,
            max_ms: 0,
            histogram: vec![0; HISTOGRAM_BUCKETS.len()],
        }
    }

    fn record(&mut self, duration_ms: u64, is_error: bool) {
        self.count += 1;
        self.total_ms += duration_ms;
        if duration_ms > self.max_ms {
            self.max_ms = duration_ms;
        }
        if is_error {
            self.errors += 1;
        }
        for (i, &boundary) in HISTOGRAM_BUCKETS.iter().enumerate() {
            if duration_ms <= boundary {
                self.histogram[i] += 1;
            }
        }
    }

    pub fn avg_ms(&self) -> f64 {
        if self.count == 0 {
            0.0
        } else {
            self.total_ms as f64 / self.count as f64
        }
    }
}

pub fn record_request(path: &str, duration_ms: u64, is_error: bool) {
    TOTAL_REQUESTS.fetch_add(1, Ordering::Relaxed);
    if is_error {
        TOTAL_ERRORS.fetch_add(1, Ordering::Relaxed);
    }
    let normalised = normalise_path(path);
    if let Ok(mut guard) = ENDPOINT_METRICS.write() {
        let map = guard.get_or_insert_with(HashMap::new);
        map.entry(normalised)
            .or_insert_with(EndpointStats::new)
            .record(duration_ms, is_error);
    }
}

fn normalise_path(path: &str) -> String {
    path.split('/')
        .map(|seg| {
            if !seg.is_empty() && seg.chars().all(|c| c.is_ascii_digit()) {
                ":id"
            } else {
                seg
            }
        })
        .collect::<Vec<_>>()
        .join("/")
}

/// JSON snapshot of all telemetry data.
pub fn snapshot() -> Value {
    let total = TOTAL_REQUESTS.load(Ordering::Relaxed);
    let errors = TOTAL_ERRORS.load(Ordering::Relaxed);
    let endpoints: Vec<Value> = match ENDPOINT_METRICS.read() {
        Ok(guard) => guard
            .as_ref()
            .map(|map| {
                let mut entries: Vec<_> = map.iter().collect();
                entries.sort_by(|a, b| b.1.count.cmp(&a.1.count));
                entries
                    .iter()
                    .map(|(path, stats)| {
                        json!({
                            "path": path,
                            "count": stats.count,
                            "errors": stats.errors,
                            "avg_ms": (stats.avg_ms() * 100.0).round() / 100.0,
                            "max_ms": stats.max_ms,
                        })
                    })
                    .collect()
            })
            .unwrap_or_default(),
        Err(_) => vec![],
    };
    json!({
        "total_requests": total,
        "total_errors": errors,
        "error_rate": if total > 0 {
            (errors as f64 / total as f64 * 10000.0).round() / 100.0
        } else { 0.0 },
        "endpoints": endpoints,
    })
}

/// Reset all counters (for testing).
pub fn reset() {
    TOTAL_REQUESTS.store(0, Ordering::Relaxed);
    TOTAL_ERRORS.store(0, Ordering::Relaxed);
    if let Ok(mut guard) = ENDPOINT_METRICS.write() {
        *guard = None;
    }
}

/// Axum middleware: records request count and response time.
pub async fn telemetry_layer(mut req: Request<Body>, next: Next) -> Response {
    let path = req.uri().path().to_string();
    let request_id = req
        .headers()
        .get(REQUEST_ID_HEADER)
        .and_then(|v| v.to_str().ok())
        .filter(|v| !v.trim().is_empty())
        .map(str::to_owned)
        .unwrap_or_else(|| uuid::Uuid::new_v4().to_string());
    req.extensions_mut().insert(request_id.clone());
    let start = Instant::now();
    let mut response = next.run(req).await;
    let duration_ms = start.elapsed().as_millis() as u64;
    let is_error = response.status().is_client_error() || response.status().is_server_error();
    if let Ok(hv) = request_id.parse() {
        response
            .headers_mut()
            .insert(HeaderName::from_static(REQUEST_ID_HEADER), hv);
    }
    record_request(&path, duration_ms, is_error);
    response
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn path_normalisation() {
        assert_eq!(normalise_path("/api/plans/42"), "/api/plans/:id");
        assert_eq!(normalise_path("/api/health"), "/api/health");
    }

    #[test]
    fn record_and_snapshot() {
        reset();
        record_request("/api/plans", 50, false);
        record_request("/api/plans", 200, true);
        let snap = snapshot();
        assert_eq!(snap["total_requests"], 2);
        assert_eq!(snap["total_errors"], 1);
    }

    #[test]
    fn endpoint_stats_avg() {
        let mut stats = EndpointStats::new();
        stats.record(100, false);
        stats.record(200, false);
        assert!((stats.avg_ms() - 150.0).abs() < 0.01);
    }
}
