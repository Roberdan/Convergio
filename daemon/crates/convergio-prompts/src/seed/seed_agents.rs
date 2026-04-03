//! Seed the 70 default agent prompts with metadata.

use rusqlite::{params, Connection};

use super::seed_data_1;
use super::seed_data_2;
use super::seed_data_3;

/// Agent metadata: (file_name, category, model, max_turns, tools).
pub struct AgentMeta {
    pub name: &'static str,
    pub category: &'static str,
    pub model: &'static str,
    pub max_turns: u32,
    pub tools: &'static str,
    pub body: &'static str,
}

pub fn seed(conn: &Connection) -> Result<(), String> {
    let batches: &[&[AgentMeta]] = &[
        seed_data_1::AGENTS,
        seed_data_2::AGENTS,
        seed_data_3::AGENTS,
    ];
    let mut count = 0u32;
    for batch in batches {
        for agent in *batch {
            let id = format!("pt-seed-agent-{}", agent.name);
            let category = format!("agent-{}", agent.category);
            let vars_json = build_vars_json(agent);
            conn.execute(
                "INSERT OR IGNORE INTO prompt_templates \
                 (id, name, version, body, variables, category, active) \
                 VALUES (?1, ?2, 1, ?3, ?4, ?5, 1)",
                params![
                    id,
                    format!("agent-{}", agent.name),
                    agent.body,
                    vars_json,
                    category,
                ],
            )
            .map_err(|e| format!("seed agent {}: {e}", agent.name))?;
            count += 1;
        }
    }
    tracing::debug!("Seeded {count} agent prompts");
    Ok(())
}

fn build_vars_json(agent: &AgentMeta) -> String {
    format!(
        r#"[{{"name":"model","description":"Preferred model","required":false,"default_value":"{}"}},{{"name":"max_turns","description":"Max conversation turns","required":false,"default_value":"{}"}},{{"name":"tools","description":"Available tools","required":false,"default_value":"{}"}}]"#,
        agent.model, agent.max_turns, agent.tools,
    )
}
