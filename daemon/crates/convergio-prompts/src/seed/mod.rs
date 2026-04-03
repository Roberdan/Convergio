//! Idempotent seed for default prompts, agents, and pipeline.
//!
//! Called from `on_start()`. Uses INSERT OR IGNORE so re-runs are no-ops.

use rusqlite::{params, Connection};

use crate::types::PipelineStep;

mod seed_agents;
mod seed_data_1;
mod seed_data_2;
mod seed_data_3;
mod seed_skills;

const SENTINEL: &str = "_cvg_seed_v1";

/// Run the seed. Skips if the sentinel prompt already exists.
pub fn run(conn: &Connection) -> Result<(), String> {
    let seeded: bool = conn
        .query_row(
            "SELECT count(*) > 0 FROM prompt_templates WHERE name = ?1",
            params![SENTINEL],
            |r| r.get(0),
        )
        .map_err(|e| e.to_string())?;

    if seeded {
        tracing::debug!("Prompt seed already applied, skipping");
        return Ok(());
    }

    tracing::info!("Seeding default prompts and pipeline...");

    seed_skills::seed(conn)?;
    seed_agents::seed(conn)?;
    seed_default_pipeline(conn)?;

    // Plant sentinel.
    conn.execute(
        "INSERT OR IGNORE INTO prompt_templates \
         (id, name, version, body, variables, category, active) \
         VALUES (?1, ?2, 1, 'seed marker', '[]', 'internal', 1)",
        params![format!("pt-seed-{SENTINEL}"), SENTINEL],
    )
    .map_err(|e| e.to_string())?;

    tracing::info!("Prompt seed complete");
    Ok(())
}

fn seed_default_pipeline(conn: &Connection) -> Result<(), String> {
    let steps = vec![
        PipelineStep {
            order: 1,
            skill: "solve".into(),
            prompt_name: "skill-solve".into(),
            agent: None,
            condition: None,
        },
        PipelineStep {
            order: 2,
            skill: "planner".into(),
            prompt_name: "skill-planner".into(),
            agent: None,
            condition: None,
        },
        PipelineStep {
            order: 3,
            skill: "execute".into(),
            prompt_name: "skill-execute".into(),
            agent: None,
            condition: None,
        },
        PipelineStep {
            order: 4,
            skill: "validate".into(),
            prompt_name: "agent-thor-quality-assurance-guardian".into(),
            agent: Some("thor".into()),
            condition: None,
        },
    ];
    let steps_json = serde_json::to_string(&steps).unwrap_or_default();
    conn.execute(
        "INSERT OR IGNORE INTO prompt_pipelines \
         (id, name, description, steps_json, active) \
         VALUES ('pl-seed-default', 'default-workflow', \
         'Standard solve → planner → execute → validate pipeline', ?1, 1)",
        params![steps_json],
    )
    .map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "prompts", &crate::schema::migrations())
            .unwrap();
        conn
    }

    #[test]
    fn seed_populates_prompts() {
        let conn = setup();
        run(&conn).unwrap();
        let count: i64 = conn
            .query_row(
                "SELECT count(*) FROM prompt_templates WHERE active = 1",
                [],
                |r| r.get(0),
            )
            .unwrap();
        // 8 skills + 70 agents + 1 sentinel = 79
        assert!(count >= 79, "expected >= 79 prompts, got {count}");
    }

    #[test]
    fn seed_is_idempotent() {
        let conn = setup();
        run(&conn).unwrap();
        let c1: i64 = conn
            .query_row("SELECT count(*) FROM prompt_templates", [], |r| r.get(0))
            .unwrap();
        run(&conn).unwrap();
        let c2: i64 = conn
            .query_row("SELECT count(*) FROM prompt_templates", [], |r| r.get(0))
            .unwrap();
        assert_eq!(c1, c2, "seed should be idempotent");
    }

    #[test]
    fn seed_creates_default_pipeline() {
        let conn = setup();
        run(&conn).unwrap();
        let name: String = conn
            .query_row(
                "SELECT name FROM prompt_pipelines WHERE id = 'pl-seed-default'",
                [],
                |r| r.get(0),
            )
            .unwrap();
        assert_eq!(name, "default-workflow");
    }
}
