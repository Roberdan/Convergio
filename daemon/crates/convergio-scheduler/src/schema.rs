//! DB migrations for scheduler tables.

use convergio_types::extension::Migration;

pub fn migrations() -> Vec<Migration> {
    vec![Migration {
        version: 1,
        description: "scheduler policies and decision history",
        up: "
            CREATE TABLE IF NOT EXISTS scheduler_policies (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                name             TEXT    NOT NULL UNIQUE,
                weight_capability REAL   NOT NULL DEFAULT 0.4,
                weight_cost      REAL    NOT NULL DEFAULT 0.2,
                weight_load      REAL    NOT NULL DEFAULT 0.2,
                weight_locality  REAL    NOT NULL DEFAULT 0.2,
                privacy_enforce  INTEGER NOT NULL DEFAULT 1,
                created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scheduling_decisions (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id        INTEGER NOT NULL,
                plan_id        INTEGER NOT NULL,
                assigned_peer  TEXT    NOT NULL,
                assigned_tier  TEXT    NOT NULL,
                estimated_cost REAL    NOT NULL DEFAULT 0,
                reason         TEXT    NOT NULL DEFAULT '',
                decided_at     TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_sched_decisions_task
                ON scheduling_decisions(task_id);
            CREATE INDEX IF NOT EXISTS idx_sched_decisions_plan
                ON scheduling_decisions(plan_id);
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
            convergio_db::migration::apply_migrations(&conn, "scheduler", &migrations()).unwrap();
        assert_eq!(applied, 1);
    }
}
