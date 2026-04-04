// Migration v13 — Evaluation framework tables.
// WHY: Track planner quality and Thor review accuracy so the
// orchestration pipeline can be measured and improved.

use convergio_types::extension::Migration;

pub fn evaluation_migrations() -> Vec<Migration> {
    vec![Migration {
        version: 13,
        description: "evaluation framework for planner and Thor",
        up: "CREATE TABLE IF NOT EXISTS plan_evaluations (\
                 id              INTEGER PRIMARY KEY AUTOINCREMENT,\
                 plan_id         INTEGER NOT NULL,\
                 evaluator       TEXT NOT NULL DEFAULT 'system',\
                 tasks_total     INTEGER NOT NULL DEFAULT 0,\
                 tasks_completed INTEGER NOT NULL DEFAULT 0,\
                 tasks_failed    INTEGER NOT NULL DEFAULT 0,\
                 false_positives INTEGER NOT NULL DEFAULT 0,\
                 false_negatives INTEGER NOT NULL DEFAULT 0,\
                 precision_score REAL NOT NULL DEFAULT 0,\
                 recall_score    REAL NOT NULL DEFAULT 0,\
                 f1_score        REAL NOT NULL DEFAULT 0,\
                 total_cost_usd  REAL NOT NULL DEFAULT 0,\
                 total_duration_secs INTEGER NOT NULL DEFAULT 0,\
                 evaluated_at    TEXT NOT NULL DEFAULT (datetime('now'))\
             );\
             CREATE INDEX IF NOT EXISTS idx_evaluations_plan \
                 ON plan_evaluations(plan_id);\
             CREATE TABLE IF NOT EXISTS review_outcomes (\
                 id              INTEGER PRIMARY KEY AUTOINCREMENT,\
                 plan_id         INTEGER NOT NULL,\
                 task_id         INTEGER NOT NULL,\
                 thor_decision   TEXT NOT NULL,\
                 actual_outcome  TEXT NOT NULL,\
                 is_correct      INTEGER NOT NULL DEFAULT 0,\
                 recorded_at     TEXT NOT NULL DEFAULT (datetime('now'))\
             );\
             CREATE INDEX IF NOT EXISTS idx_review_outcomes_plan \
                 ON review_outcomes(plan_id);",
    }]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn evaluation_migrations_apply_cleanly() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        let base = crate::schema::migrations();
        convergio_db::migration::apply_migrations(&conn, "orchestrator", &base).unwrap();
        let tracking = crate::schema_tracking::tracking_migrations();
        convergio_db::migration::apply_migrations(&conn, "orchestrator", &tracking).unwrap();
        let eval = evaluation_migrations();
        let applied =
            convergio_db::migration::apply_migrations(&conn, "orchestrator", &eval).unwrap();
        assert_eq!(applied, 1);
    }
}
