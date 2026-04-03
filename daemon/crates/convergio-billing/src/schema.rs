//! DB migrations for billing tables.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![
        Migration {
            version: 1,
            description: "billing core tables",
            up: "
                CREATE TABLE IF NOT EXISTS billing_usage (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id     TEXT    NOT NULL,
                    agent_id   TEXT,
                    task_id    INTEGER,
                    category   TEXT    NOT NULL,
                    quantity   REAL    NOT NULL DEFAULT 0.0,
                    unit       TEXT    NOT NULL DEFAULT 'unit',
                    cost_usd   REAL    NOT NULL DEFAULT 0.0,
                    model      TEXT,
                    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_billing_usage_org
                    ON billing_usage(org_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_billing_usage_agent
                    ON billing_usage(agent_id, created_at);
            ",
        },
        Migration {
            version: 2,
            description: "budget hierarchy and rate cards",
            up: "
                CREATE TABLE IF NOT EXISTS billing_budgets (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope           TEXT    NOT NULL,
                    entity_id       TEXT    NOT NULL,
                    daily_limit_usd REAL    NOT NULL DEFAULT 50.0,
                    monthly_limit_usd REAL  NOT NULL DEFAULT 1000.0,
                    auto_pause      INTEGER NOT NULL DEFAULT 0,
                    paused          INTEGER NOT NULL DEFAULT 0,
                    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                    UNIQUE (scope, entity_id)
                );

                CREATE TABLE IF NOT EXISTS billing_rate_cards (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id         TEXT    NOT NULL,
                    capability     TEXT    NOT NULL,
                    price_per_unit REAL    NOT NULL,
                    unit           TEXT    NOT NULL DEFAULT 'request',
                    effective_from TEXT    NOT NULL DEFAULT (date('now')),
                    UNIQUE (org_id, capability)
                );
            ",
        },
        Migration {
            version: 3,
            description: "invoices, settlements, audit chain, quotas",
            up: "
                CREATE TABLE IF NOT EXISTS billing_invoices (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id       TEXT    NOT NULL,
                    period_start TEXT    NOT NULL,
                    period_end   TEXT    NOT NULL,
                    items_json   TEXT    NOT NULL DEFAULT '[]',
                    total_usd    REAL    NOT NULL DEFAULT 0.0,
                    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS billing_settlements (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_org       TEXT    NOT NULL,
                    to_org         TEXT    NOT NULL,
                    amount_usd     REAL    NOT NULL,
                    capability     TEXT    NOT NULL,
                    reference_task INTEGER,
                    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS billing_audit (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT    NOT NULL,
                    entity_id  TEXT    NOT NULL,
                    amount_usd REAL    NOT NULL DEFAULT 0.0,
                    details    TEXT    NOT NULL DEFAULT '',
                    prev_hash  TEXT    NOT NULL DEFAULT '',
                    hash       TEXT    NOT NULL DEFAULT '',
                    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_billing_audit_entity
                    ON billing_audit(entity_id, created_at);

                CREATE TABLE IF NOT EXISTS billing_quotas (
                    org_id           TEXT PRIMARY KEY,
                    daily_free_usd   REAL NOT NULL DEFAULT 0.0,
                    monthly_free_usd REAL NOT NULL DEFAULT 0.0
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
            convergio_db::migration::apply_migrations(&conn, "billing", &migrations()).unwrap();
        assert_eq!(applied, 3);
    }
}
