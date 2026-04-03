use std::collections::HashMap;

use rusqlite::params;

use crate::types::{AgentSkill, IpcResult};
use convergio_db::pool::ConnPool;

pub fn register_skills(
    pool: &ConnPool,
    agent: &str,
    host: &str,
    skills: &[(&str, f64)],
) -> IpcResult<()> {
    let conn = pool.get()?;
    for (skill, confidence) in skills {
        conn.execute(
            "INSERT OR REPLACE INTO ipc_agent_skills (agent, host, skill, confidence, last_used)
             VALUES (?1, ?2, ?3, ?4, strftime('%Y-%m-%dT%H:%M:%f','now'))",
            params![agent, host, skill, confidence],
        )?;
    }
    Ok(())
}

pub fn update_skill_usage(
    pool: &ConnPool,
    agent: &str,
    host: &str,
    skill: &str,
) -> IpcResult<()> {
    let conn = pool.get()?;
    conn.execute(
        "UPDATE ipc_agent_skills SET last_used = strftime('%Y-%m-%dT%H:%M:%f','now')
         WHERE agent = ?1 AND host = ?2 AND skill = ?3",
        params![agent, host, skill],
    )?;
    Ok(())
}

pub fn unregister_agent_skills(pool: &ConnPool, agent: &str, host: &str) -> IpcResult<usize> {
    let conn = pool.get()?;
    let deleted = conn.execute(
        "DELETE FROM ipc_agent_skills WHERE agent = ?1 AND host = ?2",
        params![agent, host],
    )?;
    Ok(deleted)
}

pub fn get_skill_pool(pool: &ConnPool) -> IpcResult<HashMap<String, Vec<AgentSkill>>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT agent, host, skill, confidence, last_used
         FROM ipc_agent_skills ORDER BY skill, confidence DESC",
    )?;
    let rows = stmt
        .query_map([], map_skill)?
        .filter_map(|r| r.ok());
    let mut result: HashMap<String, Vec<AgentSkill>> = HashMap::new();
    for skill in rows {
        result.entry(skill.skill.clone()).or_default().push(skill);
    }
    Ok(result)
}

pub fn get_agents_for_skill(pool: &ConnPool, skill: &str) -> IpcResult<Vec<AgentSkill>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT agent, host, skill, confidence, last_used
         FROM ipc_agent_skills WHERE skill = ?1 ORDER BY confidence DESC",
    )?;
    let skills = stmt
        .query_map(params![skill], map_skill)?
        .filter_map(|r| r.ok())
        .collect();
    Ok(skills)
}

pub fn get_skills_for_agent(pool: &ConnPool, agent: &str) -> IpcResult<Vec<AgentSkill>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT agent, host, skill, confidence, last_used
         FROM ipc_agent_skills WHERE agent = ?1 ORDER BY skill",
    )?;
    let skills = stmt
        .query_map(params![agent], map_skill)?
        .filter_map(|r| r.ok())
        .collect();
    Ok(skills)
}

pub fn find_best_agent(pool: &ConnPool, skill: &str) -> IpcResult<Option<(String, String)>> {
    let conn = pool.get()?;
    let result = conn.query_row(
        "SELECT agent, host FROM ipc_agent_skills
         WHERE skill = ?1 AND agent != '' ORDER BY confidence DESC LIMIT 1",
        params![skill],
        |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)),
    );
    match result {
        Ok(r) => Ok(Some(r)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(e.into()),
    }
}

pub fn update_confidence(
    pool: &ConnPool,
    agent: &str,
    host: &str,
    skill: &str,
    rating: f64,
) -> IpcResult<()> {
    let conn = pool.get()?;
    let current: f64 = conn
        .query_row(
            "SELECT confidence FROM ipc_agent_skills
             WHERE agent = ?1 AND host = ?2 AND skill = ?3",
            params![agent, host, skill],
            |r| r.get(0),
        )
        .unwrap_or(0.5);
    let updated = current * 0.8 + rating * 0.2;
    conn.execute(
        "UPDATE ipc_agent_skills SET confidence = ?1
         WHERE agent = ?2 AND host = ?3 AND skill = ?4",
        params![updated, agent, host, skill],
    )?;
    Ok(())
}

fn map_skill(row: &rusqlite::Row<'_>) -> rusqlite::Result<AgentSkill> {
    Ok(AgentSkill {
        agent: row.get(0)?,
        host: row.get(1)?,
        skill: row.get(2)?,
        confidence: row.get(3)?,
        last_used: row.get(4)?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pool() -> ConnPool {
        let p = convergio_db::pool::create_memory_pool().unwrap();
        let conn = p.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "ipc", &crate::schema::migrations())
            .unwrap();
        p
    }

    #[test]
    fn register_and_query_skills() {
        let p = pool();
        register_skills(&p, "elena", "m5max", &[("legal-review", 0.9), ("drafting", 0.7)])
            .unwrap();
        let skills = get_skills_for_agent(&p, "elena").unwrap();
        assert_eq!(skills.len(), 2);
    }

    #[test]
    fn find_best_agent_by_skill() {
        let p = pool();
        register_skills(&p, "elena", "m5max", &[("legal-review", 0.9)]).unwrap();
        register_skills(&p, "baccio", "m1pro", &[("legal-review", 0.7)]).unwrap();
        let best = find_best_agent(&p, "legal-review").unwrap().unwrap();
        assert_eq!(best.0, "elena");
    }

    #[test]
    fn confidence_update_weighted() {
        let p = pool();
        register_skills(&p, "elena", "m5max", &[("review", 0.5)]).unwrap();
        update_confidence(&p, "elena", "m5max", "review", 1.0).unwrap();
        let skills = get_skills_for_agent(&p, "elena").unwrap();
        let conf = skills[0].confidence;
        assert!((conf - 0.6).abs() < 0.01); // 0.5*0.8 + 1.0*0.2 = 0.6
    }

    #[test]
    fn skill_pool_grouped() {
        let p = pool();
        register_skills(&p, "elena", "m5max", &[("review", 0.9)]).unwrap();
        register_skills(&p, "baccio", "m1pro", &[("review", 0.7), ("coding", 0.8)]).unwrap();
        let pool_map = get_skill_pool(&p).unwrap();
        assert_eq!(pool_map["review"].len(), 2);
        assert_eq!(pool_map["coding"].len(), 1);
    }
}
