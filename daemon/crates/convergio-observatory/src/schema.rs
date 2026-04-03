//! DB migrations for observatory tables.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "observatory timeline and search",
            up: "
                CREATE TABLE IF NOT EXISTS obs_timeline (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    source       TEXT    NOT NULL,
                    event_type   TEXT    NOT NULL,
                    actor        TEXT    NOT NULL DEFAULT '',
                    org_id       TEXT,
                    node_id      TEXT,
                    summary      TEXT    NOT NULL DEFAULT '',
                    details_json TEXT,
                    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_obs_timeline_org
                    ON obs_timeline(org_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_obs_timeline_source
                    ON obs_timeline(source, created_at);
                CREATE INDEX IF NOT EXISTS idx_obs_timeline_type
                    ON obs_timeline(event_type, created_at);

                CREATE VIRTUAL TABLE IF NOT EXISTS obs_search
                    USING fts5(source, event_type, actor, summary, details);
            ",
        },
        Migration {
            version: 2,
            description: "anomaly detection and dashboard cache",
            up: "
                CREATE TABLE IF NOT EXISTS obs_anomalies (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind        TEXT    NOT NULL,
                    severity    TEXT    NOT NULL DEFAULT 'medium',
                    entity_id   TEXT    NOT NULL,
                    description TEXT    NOT NULL DEFAULT '',
                    detected_at TEXT    NOT NULL DEFAULT (datetime('now')),
                    resolved    INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_obs_anomalies_kind
                    ON obs_anomalies(kind, detected_at);

                CREATE TABLE IF NOT EXISTS obs_dashboard_cache (
                    key        TEXT    PRIMARY KEY,
                    value_json TEXT    NOT NULL,
                    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS obs_webhooks (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    url        TEXT    NOT NULL,
                    event_filter TEXT  NOT NULL DEFAULT '*',
                    active     INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
                );
            ",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn migrations_are_ordered() {
        let m = migrations();
        for (i, mig) in m.iter().enumerate() {
            assert_eq!(mig.version, (i + 1) as u32);
        }
    }

    #[test]
    fn migrations_apply_cleanly() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        let applied =
            convergio_db::migration::apply_migrations(&conn, "observatory", &migrations()).unwrap();
        assert_eq!(applied, 2);
    }
}
