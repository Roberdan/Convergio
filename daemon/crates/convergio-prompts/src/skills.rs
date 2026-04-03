//! Skill registry — agents declare capabilities, system does discovery.

use rusqlite::{params, Connection};

use crate::types::{Skill, SkillInput, SkillQuery};

/// Register or update a skill for an agent.
pub fn register_skill(conn: &Connection, input: &SkillInput) -> rusqlite::Result<String> {
    let id = format!("sk-{}", &uuid_short());
    conn.execute(
        "INSERT INTO prompt_skills (id, agent, host, capability, confidence, description)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)
         ON CONFLICT(agent, host, capability)
         DO UPDATE SET confidence = excluded.confidence,
                       description = excluded.description,
                       last_used = strftime('%Y-%m-%dT%H:%M:%f','now')",
        params![
            id,
            input.agent,
            input.host,
            input.capability,
            input.confidence,
            input.description
        ],
    )?;
    // Return the actual ID (may be the existing one on conflict).
    let actual_id: String = conn.query_row(
        "SELECT id FROM prompt_skills WHERE agent = ?1 AND host = ?2 AND capability = ?3",
        params![input.agent, input.host, input.capability],
        |r| r.get(0),
    )?;
    Ok(actual_id)
}

/// Remove all skills for an agent on a host.
pub fn unregister_agent(conn: &Connection, agent: &str, host: &str) -> rusqlite::Result<usize> {
    conn.execute(
        "DELETE FROM prompt_skills WHERE agent = ?1 AND host = ?2",
        params![agent, host],
    )
}

/// Search skills with optional filters.
pub fn search_skills(conn: &Connection, query: &SkillQuery) -> rusqlite::Result<Vec<Skill>> {
    let mut sql = String::from(
        "SELECT id, agent, host, capability, confidence, description, last_used, registered_at
         FROM prompt_skills WHERE 1=1",
    );
    let mut param_values: Vec<Box<dyn rusqlite::types::ToSql>> = vec![];

    if let Some(ref cap) = query.capability {
        sql.push_str(&format!(" AND capability = ?{}", param_values.len() + 1));
        param_values.push(Box::new(cap.clone()));
    }
    if let Some(ref agent) = query.agent {
        sql.push_str(&format!(" AND agent = ?{}", param_values.len() + 1));
        param_values.push(Box::new(agent.clone()));
    }
    if let Some(min_conf) = query.min_confidence {
        sql.push_str(&format!(" AND confidence >= ?{}", param_values.len() + 1));
        param_values.push(Box::new(min_conf));
    }
    sql.push_str(" ORDER BY capability, confidence DESC");

    let refs: Vec<&dyn rusqlite::types::ToSql> = param_values.iter().map(|b| b.as_ref()).collect();
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(refs.as_slice(), row_to_skill)?;
    rows.collect()
}

/// Find the best agent for a given capability (highest confidence).
pub fn find_best_agent(conn: &Connection, capability: &str) -> rusqlite::Result<Option<Skill>> {
    let result = conn.query_row(
        "SELECT id, agent, host, capability, confidence, description, last_used, registered_at
         FROM prompt_skills WHERE capability = ?1 ORDER BY confidence DESC LIMIT 1",
        params![capability],
        row_to_skill,
    );
    match result {
        Ok(s) => Ok(Some(s)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e),
    }
}

/// Update the last_used timestamp for a skill.
pub fn touch_skill(
    conn: &Connection,
    agent: &str,
    host: &str,
    capability: &str,
) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE prompt_skills SET last_used = strftime('%Y-%m-%dT%H:%M:%f','now')
         WHERE agent = ?1 AND host = ?2 AND capability = ?3",
        params![agent, host, capability],
    )?;
    Ok(())
}

/// Update confidence via weighted moving average (80% old + 20% rating).
pub fn update_confidence(
    conn: &Connection,
    agent: &str,
    host: &str,
    capability: &str,
    rating: f64,
) -> rusqlite::Result<()> {
    let current: f64 = conn
        .query_row(
            "SELECT confidence FROM prompt_skills WHERE agent=?1 AND host=?2 AND capability=?3",
            params![agent, host, capability],
            |r| r.get(0),
        )
        .unwrap_or(0.5);
    let updated = current * 0.8 + rating * 0.2;
    conn.execute(
        "UPDATE prompt_skills SET confidence = ?1 WHERE agent=?2 AND host=?3 AND capability=?4",
        params![updated, agent, host, capability],
    )?;
    Ok(())
}

fn row_to_skill(row: &rusqlite::Row) -> rusqlite::Result<Skill> {
    Ok(Skill {
        id: row.get(0)?,
        agent: row.get(1)?,
        host: row.get(2)?,
        capability: row.get(3)?,
        confidence: row.get(4)?,
        description: row.get(5)?,
        last_used: row.get(6)?,
        registered_at: row.get(7)?,
    })
}

fn uuid_short() -> String {
    uuid::Uuid::new_v4().to_string()[..8].to_string()
}

#[cfg(test)]
#[path = "skills_tests.rs"]
mod tests;
