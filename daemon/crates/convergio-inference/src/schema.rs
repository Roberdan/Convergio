//! DB migrations for inference token tracking tables.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![Migration {
        version: 1,
        description: "inference cost tracking tables",
        up: "
            CREATE TABLE IF NOT EXISTS inference_costs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id      TEXT    NOT NULL,
                org_id        TEXT,
                plan_id       INTEGER,
                model         TEXT    NOT NULL,
                tokens_input  INTEGER NOT NULL DEFAULT 0,
                tokens_output INTEGER NOT NULL DEFAULT 0,
                cost_usd      REAL    NOT NULL DEFAULT 0.0,
                created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_costs_agent
                ON inference_costs(agent_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_costs_org
                ON inference_costs(org_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_costs_plan
                ON inference_costs(plan_id);

            CREATE TABLE IF NOT EXISTS inference_budgets (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type         TEXT    NOT NULL,
                entity_id           TEXT    NOT NULL,
                daily_token_limit   INTEGER NOT NULL DEFAULT 10000000,
                daily_cost_limit    REAL    NOT NULL DEFAULT 50.0,
                downgrade_threshold REAL    NOT NULL DEFAULT 0.8,
                created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE (entity_type, entity_id)
            );
        ",
    }]
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
            convergio_db::migration::apply_migrations(&conn, "inference", &migrations()).unwrap();
        assert_eq!(applied, 1);
    }
}
