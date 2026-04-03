//! Prompt injection at spawn — frozen, immutable prompts for agent execution.
//!
//! When the daemon spawns an agent, the prompt includes current operational rules.
//! Once spawned, the prompt is immutable for the entire task duration.

use std::collections::HashMap;

use rusqlite::{params, Connection};

use crate::render;
use crate::store;
use crate::types::SpawnedPrompt;

/// Build and freeze a prompt for an agent spawn.
///
/// Renders the template with the provided variables, persists an immutable
/// snapshot, and returns it. Changes to the template after this point do
/// not affect this execution.
pub fn inject_at_spawn(
    conn: &Connection,
    prompt_name: &str,
    agent: &str,
    task_id: &str,
    values: &HashMap<String, String>,
) -> Result<SpawnedPrompt, String> {
    let template = store::get_active_prompt(conn, prompt_name)
        .map_err(|e| format!("prompt not found: {e}"))?;

    let rendered = render::render(&template.body, &template.variables, values)?;
    let spawn_id = format!("sp-{}", uuid_short());

    conn.execute(
        "INSERT INTO prompt_spawned (spawn_id, agent, task_id, rendered_body, prompt_template_id, prompt_version)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![spawn_id, agent, task_id, rendered, template.id, template.version],
    )
    .map_err(|e| format!("failed to persist spawn: {e}"))?;

    let spawned_at: String = conn
        .query_row(
            "SELECT spawned_at FROM prompt_spawned WHERE spawn_id = ?1",
            params![spawn_id],
            |r| r.get(0),
        )
        .unwrap_or_default();

    Ok(SpawnedPrompt {
        spawn_id,
        agent: agent.into(),
        task_id: task_id.into(),
        rendered_body: rendered,
        prompt_template_id: template.id,
        prompt_version: template.version,
        spawned_at,
    })
}

/// Retrieve the immutable prompt for an active execution.
pub fn get_spawned(conn: &Connection, spawn_id: &str) -> rusqlite::Result<SpawnedPrompt> {
    conn.query_row(
        "SELECT spawn_id, agent, task_id, rendered_body, prompt_template_id, prompt_version, spawned_at
         FROM prompt_spawned WHERE spawn_id = ?1",
        params![spawn_id],
        |row| {
            Ok(SpawnedPrompt {
                spawn_id: row.get(0)?,
                agent: row.get(1)?,
                task_id: row.get(2)?,
                rendered_body: row.get(3)?,
                prompt_template_id: row.get(4)?,
                prompt_version: row.get(5)?,
                spawned_at: row.get(6)?,
            })
        },
    )
}

/// Get all spawned prompts for a task (useful for audit).
pub fn get_spawned_for_task(conn: &Connection, task_id: &str) -> rusqlite::Result<Vec<SpawnedPrompt>> {
    let mut stmt = conn.prepare(
        "SELECT spawn_id, agent, task_id, rendered_body, prompt_template_id, prompt_version, spawned_at
         FROM prompt_spawned WHERE task_id = ?1 ORDER BY spawned_at",
    )?;
    let rows = stmt.query_map(params![task_id], |row| {
        Ok(SpawnedPrompt {
            spawn_id: row.get(0)?,
            agent: row.get(1)?,
            task_id: row.get(2)?,
            rendered_body: row.get(3)?,
            prompt_template_id: row.get(4)?,
            prompt_version: row.get(5)?,
            spawned_at: row.get(6)?,
        })
    })?;
    rows.collect()
}

fn uuid_short() -> String {
    uuid::Uuid::new_v4().to_string()[..8].to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{PromptInput, PromptVariable};

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "prompts", &crate::schema::migrations())
            .unwrap();
        conn
    }

    #[test]
    fn spawn_freezes_prompt() {
        let conn = setup();
        store::create_prompt(&conn, &PromptInput {
            name: "agent-system".into(),
            body: "You are {{role}}. Rules: {{rules}}".into(),
            variables: vec![
                PromptVariable {
                    name: "role".into(), description: "Agent role".into(),
                    required: true, default_value: None,
                },
                PromptVariable {
                    name: "rules".into(), description: "Rules".into(),
                    required: true, default_value: None,
                },
            ],
            category: Some("system".into()),
        }).unwrap();

        let mut values = HashMap::new();
        values.insert("role".into(), "legal reviewer".into());
        values.insert("rules".into(), "max 250 lines, conventional commits".into());

        let spawned = inject_at_spawn(&conn, "agent-system", "elena", "task-7", &values).unwrap();
        assert!(spawned.rendered_body.contains("legal reviewer"));
        assert!(spawned.rendered_body.contains("conventional commits"));

        // Updating the template does NOT affect the frozen spawn.
        store::create_prompt(&conn, &PromptInput {
            name: "agent-system".into(),
            body: "CHANGED template".into(),
            variables: vec![],
            category: Some("system".into()),
        }).unwrap();

        let frozen = get_spawned(&conn, &spawned.spawn_id).unwrap();
        assert!(frozen.rendered_body.contains("legal reviewer"));
        assert!(!frozen.rendered_body.contains("CHANGED"));
    }

    #[test]
    fn get_spawned_for_task_returns_all() {
        let conn = setup();
        store::create_prompt(&conn, &PromptInput {
            name: "simple".into(),
            body: "Do {{task}}".into(),
            variables: vec![PromptVariable {
                name: "task".into(), description: "Task".into(),
                required: true, default_value: None,
            }],
            category: None,
        }).unwrap();

        let mut v1 = HashMap::new();
        v1.insert("task".into(), "review".into());
        inject_at_spawn(&conn, "simple", "agent-a", "task-10", &v1).unwrap();

        let mut v2 = HashMap::new();
        v2.insert("task".into(), "test".into());
        inject_at_spawn(&conn, "simple", "agent-b", "task-10", &v2).unwrap();

        let spawns = get_spawned_for_task(&conn, "task-10").unwrap();
        assert_eq!(spawns.len(), 2);
    }
}
