// Migration v11 — Compensation actions table.
// WHY: Track rollback/compensation actions when waves fail, so partial
// work can be undone automatically or reviewed manually.

use convergio_types::extension::Migration;

pub fn compensation_migrations() -> Vec<Migration> {
    vec![Migration {
        version: 11,
        description: "compensation actions for wave rollback",
        up: "CREATE TABLE IF NOT EXISTS compensation_actions (\
                 id              INTEGER PRIMARY KEY AUTOINCREMENT,\
                 plan_id         INTEGER NOT NULL,\
                 wave_id         INTEGER NOT NULL,\
                 task_id         INTEGER NOT NULL,\
                 action_type     TEXT NOT NULL,\
                 target          TEXT NOT NULL DEFAULT '',\
                 status          TEXT NOT NULL DEFAULT 'pending',\
                 error_message   TEXT,\
                 created_at      TEXT NOT NULL DEFAULT (datetime('now')),\
                 completed_at    TEXT\
             );\
             CREATE INDEX IF NOT EXISTS idx_compensations_wave \
                 ON compensation_actions(wave_id);\
             CREATE INDEX IF NOT EXISTS idx_compensations_plan \
                 ON compensation_actions(plan_id);\
             CREATE INDEX IF NOT EXISTS idx_compensations_status \
                 ON compensation_actions(status);",
    }]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compensation_migration_applies_cleanly() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        // Apply all migrations sorted by version (same as production ext.migrations())
        let mut all = crate::schema::migrations();
        all.extend(crate::schema_tracking::tracking_migrations());
        all.extend(compensation_migrations());
        all.sort_by_key(|m| m.version);
        let applied =
            convergio_db::migration::apply_migrations(&conn, "orchestrator", &all).unwrap();
        assert!(applied >= 1, "at least one migration should apply");
        // Verify compensation table exists
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='compensation_actions'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(count, 1);
    }
}
