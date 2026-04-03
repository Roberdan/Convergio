//! Per-client, per-category rate limiter with sliding window.

use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;

type BucketKey = (String, String);

#[derive(Clone)]
pub struct RateLimiter {
    buckets: Arc<Mutex<HashMap<BucketKey, Vec<Instant>>>>,
}

impl Default for RateLimiter {
    fn default() -> Self {
        Self {
            buckets: Arc::new(Mutex::new(HashMap::new())),
        }
    }
}

impl RateLimiter {
    pub async fn allow(
        &self,
        category: String,
        client_ip: String,
        limit: usize,
        window: Duration,
    ) -> bool {
        let now = Instant::now();
        let mut buckets = self.buckets.lock().await;
        let key: BucketKey = (category, client_ip);
        let entries = buckets.entry(key).or_default();
        entries.retain(|seen| now.duration_since(*seen) <= window);
        if entries.len() >= limit {
            return false;
        }
        entries.push(now);
        if buckets.len() > 10_000 {
            buckets.retain(|_, v| !v.is_empty());
        }
        true
    }
}

pub fn endpoint_category(path: &str) -> String {
    let mut segments = path.split('/').filter(|s| !s.is_empty());
    match (segments.next(), segments.next()) {
        (Some("api"), Some(cat)) => format!("api:{cat}"),
        (Some(seg), _) => seg.to_string(),
        _ => "root".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn category_extraction() {
        assert_eq!(endpoint_category("/api/plans/1"), "api:plans");
        assert_eq!(endpoint_category("/health"), "health");
        assert_eq!(endpoint_category("/"), "root");
    }

    #[tokio::test]
    async fn rate_limiter_allows_within_limit() {
        let rl = RateLimiter::default();
        let window = Duration::from_secs(60);
        assert!(rl.allow("api:test".into(), "127.0.0.1".into(), 2, window).await);
        assert!(rl.allow("api:test".into(), "127.0.0.1".into(), 2, window).await);
        assert!(!rl.allow("api:test".into(), "127.0.0.1".into(), 2, window).await);
    }

    #[tokio::test]
    async fn different_clients_independent() {
        let rl = RateLimiter::default();
        let window = Duration::from_secs(60);
        assert!(rl.allow("cat".into(), "10.0.0.1".into(), 1, window).await);
        assert!(rl.allow("cat".into(), "10.0.0.2".into(), 1, window).await);
    }
}
