//! Seed data for the 8 core workflow skills + pipeline.
//!
//! Migrated from ConvergioPlatform/claude-config/skills/.
//! Inserted at daemon boot if not already present.

use convergio_db::pool::ConnPool;

struct SkillSeed {
    name: &'static str,
    version: u32,
    category: &'static str,
    description: &'static str,
    model: &'static str,
    triggers: &'static str,
}

const SKILLS: &[SkillSeed] = &[
    SkillSeed {
        name: "solve",
        version: 1,
        category: "workflow",
        description: "Problem understanding, triage, and consultant-style entry point",
        model: "claude-opus-4-6",
        triggers: "/solve, help me understand",
    },
    SkillSeed {
        name: "planner",
        version: 3,
        category: "workflow",
        description: "Plan creation with approval gates, Thor validation, per-task routing",
        model: "claude-opus-4-6",
        triggers: "/planner",
    },
    SkillSeed {
        name: "execute",
        version: 3,
        category: "workflow",
        description: "Automated plan task execution with per-task routing and CI batch fix",
        model: "claude-opus-4-6",
        triggers: "/execute",
    },
    SkillSeed {
        name: "research",
        version: 2,
        category: "workflow",
        description: "Investigation and analysis producing authoritative research document",
        model: "claude-opus-4-6",
        triggers: "/research",
    },
    SkillSeed {
        name: "interview",
        version: 1,
        category: "workflow",
        description: "Deep iterative one-question-at-a-time requirements extraction",
        model: "claude-opus-4-6",
        triggers: "/interview",
    },
    SkillSeed {
        name: "check",
        version: 1,
        category: "workflow",
        description: "Session state recap: git status, active plans, open PRs, next steps",
        model: "claude-sonnet-4-6",
        triggers: "/check",
    },
    SkillSeed {
        name: "prepare",
        version: 2,
        category: "workflow",
        description: "Project bootstrap: detect stack, generate CLAUDE.md, register project",
        model: "claude-opus-4-6",
        triggers: "/prepare",
    },
    SkillSeed {
        name: "release",
        version: 2,
        category: "workflow",
        description: "Pre-release validation and version management",
        model: "claude-opus-4-6",
        triggers: "/release",
    },
];

/// Seed skills into prompt_templates if not already present.
/// Returns number of inserted records.
pub fn seed(pool: &ConnPool) -> Result<usize, String> {
    let conn = pool.get().map_err(|e| e.to_string())?;
    let mut inserted = 0;
    for skill in SKILLS {
        let body = format!(
            "model: {}\ntriggers: {}\n\n{}",
            skill.model, skill.triggers, skill.description
        );
        let id = format!("skill-{}-v{}", skill.name, skill.version);
        let r = conn.execute(
            "INSERT OR IGNORE INTO prompt_templates \
             (id, name, version, body, variables, category) \
             VALUES (?1, ?2, ?3, ?4, '[]', ?5)",
            rusqlite::params![id, skill.name, skill.version, body, skill.category],
        );
        if let Ok(n) = r {
            inserted += n;
        }
    }
    // Seed the workflow pipeline: solve → planner → execute → thor
    let pipeline_id = "pipeline-workflow-v1";
    let pipeline_body = r#"{"steps":["solve","planner","execute","thor"],"description":"Standard workflow: understand → plan → execute → validate"}"#;
    if let Ok(n) = conn.execute(
        "INSERT OR IGNORE INTO prompt_pipelines \
         (id, name, steps_json, description) \
         VALUES (?1, 'workflow', ?2, 'solve → planner → execute → thor')",
        rusqlite::params![pipeline_id, pipeline_body],
    ) {
        inserted += n;
    }
    Ok(inserted)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn seed_inserts_all_skills() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        {
            let conn = pool.get().unwrap();
            convergio_db::migration::ensure_registry(&conn).unwrap();
            let migs = crate::schema::migrations();
            convergio_db::migration::apply_migrations(&conn, "prompts", &migs).unwrap();
        } // drop conn before seed() gets its own
        let inserted = seed(&pool).unwrap();
        assert_eq!(inserted, 9); // 8 skills + 1 pipeline
        let again = seed(&pool).unwrap();
        assert_eq!(again, 0);
    }
}
