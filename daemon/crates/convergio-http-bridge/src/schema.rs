//! Database schema — tables owned by convergio-http-bridge.

use convergio_types::extension::Migration;

/// V1: http_extensions table — registered external extensions.
const V1_HTTP_EXTENSIONS: &str = "\
CREATE TABLE IF NOT EXISTS http_extensions (
    id TEXT PRIMARY KEY,
    manifest_json TEXT NOT NULL,
    base_url TEXT NOT NULL,
    health_endpoint TEXT NOT NULL DEFAULT '/health',
    events_webhook TEXT NOT NULL DEFAULT '/webhook/events',
    routes_prefix TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'registered',
    registered_at TEXT NOT NULL,
    last_health_check TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_http_ext_state ON http_extensions(state);
";

/// V2: webhook delivery log for audit and retry.
const V2_WEBHOOK_LOG: &str = "\
CREATE TABLE IF NOT EXISTS http_bridge_webhook_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extension_id TEXT NOT NULL,
    event_json TEXT NOT NULL,
    delivered_at TEXT,
    status_code INTEGER,
    attempt INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    FOREIGN KEY (extension_id) REFERENCES http_extensions(id)
);
CREATE INDEX IF NOT EXISTS idx_webhook_log_ext
    ON http_bridge_webhook_log(extension_id);
";

/// All migrations for this crate.
pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "http_extensions table",
            up: V1_HTTP_EXTENSIONS,
        },
        Migration {
            version: 2,
            description: "webhook delivery log",
            up: V2_WEBHOOK_LOG,
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    use convergio_db::pool::create_memory_pool;

    #[test]
    fn migrations_apply_cleanly() {
        let pool = create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        for m in migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        // Verify tables exist
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master \
                 WHERE type='table' AND name='http_extensions'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 1);
    }

    #[test]
    fn migrations_are_ordered() {
        let migs = migrations();
        assert_eq!(migs.len(), 2);
        assert_eq!(migs[0].version, 1);
        assert_eq!(migs[1].version, 2);
    }
}
