//! Seed the 8 default skill prompts.

use rusqlite::{params, Connection};

const SKILL_CHECK: &str = include_str!("../../data/skills/check.md");
const SKILL_EXECUTE: &str = include_str!("../../data/skills/execute.md");
const SKILL_INTERVIEW: &str = include_str!("../../data/skills/interview.md");
const SKILL_PLANNER: &str = include_str!("../../data/skills/planner.md");
const SKILL_PREPARE: &str = include_str!("../../data/skills/prepare.md");
const SKILL_RELEASE: &str = include_str!("../../data/skills/release.md");
const SKILL_RESEARCH: &str = include_str!("../../data/skills/research.md");
const SKILL_SOLVE: &str = include_str!("../../data/skills/solve.md");

/// All skill prompts: (name, body).
const SKILLS: &[(&str, &str)] = &[
    ("skill-check", SKILL_CHECK),
    ("skill-execute", SKILL_EXECUTE),
    ("skill-interview", SKILL_INTERVIEW),
    ("skill-planner", SKILL_PLANNER),
    ("skill-prepare", SKILL_PREPARE),
    ("skill-release", SKILL_RELEASE),
    ("skill-research", SKILL_RESEARCH),
    ("skill-solve", SKILL_SOLVE),
];

pub fn seed(conn: &Connection) -> Result<(), String> {
    for (name, body) in SKILLS {
        let id = format!("pt-seed-{name}");
        conn.execute(
            "INSERT OR IGNORE INTO prompt_templates \
             (id, name, version, body, variables, category, active) \
             VALUES (?1, ?2, 1, ?3, '[]', 'skill', 1)",
            params![id, name, body],
        )
        .map_err(|e| format!("seed skill {name}: {e}"))?;
    }
    tracing::debug!("Seeded {} skill prompts", SKILLS.len());
    Ok(())
}
