//! CRUD operations for the agent catalog.

use rusqlite::{params, Connection};

use crate::types::{AgentCategory, AgentInput, AgentQuery, AgentSpec, AgentStatus};

/// Create a new agent catalog entry, returning its ID.
pub fn create_agent(conn: &Connection, input: &AgentInput) -> rusqlite::Result<String> {
    let id = format!("ag-{}", &uuid_short());
    let caps_json = serde_json::to_string(&input.capabilities).unwrap_or_default();
    conn.execute(
        "INSERT INTO agent_catalog
         (id, name, role, org_id, category, model_tier, max_tokens,
          hourly_budget, capabilities_json, prompt_ref, escalation_target)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
        params![
            id,
            input.name,
            input.role,
            input.org,
            input.category.as_str(),
            input.model_tier,
            input.max_tokens,
            input.hourly_budget,
            caps_json,
            input.prompt_ref,
            input.escalation_target,
        ],
    )?;
    Ok(id)
}

/// Get an agent by name.
pub fn get_agent(conn: &Connection, name: &str) -> rusqlite::Result<AgentSpec> {
    conn.query_row(
        "SELECT id, name, role, org_id, category, model_tier, max_tokens,
                hourly_budget, capabilities_json, prompt_ref, escalation_target,
                status, created_at, updated_at
         FROM agent_catalog WHERE name = ?1",
        params![name],
        row_to_agent,
    )
}

/// List agents with optional filters.
pub fn list_agents(conn: &Connection, q: &AgentQuery) -> rusqlite::Result<Vec<AgentSpec>> {
    let mut sql = String::from(
        "SELECT id, name, role, org_id, category, model_tier, max_tokens,
                hourly_budget, capabilities_json, prompt_ref, escalation_target,
                status, created_at, updated_at
         FROM agent_catalog WHERE 1=1",
    );
    let mut pv: Vec<Box<dyn rusqlite::types::ToSql>> = vec![];

    if let Some(ref cat) = q.category {
        sql.push_str(&format!(" AND category = ?{}", pv.len() + 1));
        pv.push(Box::new(cat.clone()));
    }
    if let Some(ref st) = q.status {
        sql.push_str(&format!(" AND status = ?{}", pv.len() + 1));
        pv.push(Box::new(st.clone()));
    }
    if let Some(ref name) = q.name {
        sql.push_str(&format!(" AND name = ?{}", pv.len() + 1));
        pv.push(Box::new(name.clone()));
    }
    sql.push_str(" ORDER BY category, name");

    let refs: Vec<&dyn rusqlite::types::ToSql> = pv.iter().map(|p| p.as_ref()).collect();
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(refs.as_slice(), row_to_agent)?;
    rows.collect()
}

/// Update an agent spec by name.
pub fn update_agent(conn: &Connection, name: &str, input: &AgentInput) -> rusqlite::Result<bool> {
    let caps_json = serde_json::to_string(&input.capabilities).unwrap_or_default();
    let n = conn.execute(
        "UPDATE agent_catalog SET
            role = ?1, org_id = ?2, category = ?3, model_tier = ?4,
            max_tokens = ?5, hourly_budget = ?6, capabilities_json = ?7,
            prompt_ref = ?8, escalation_target = ?9,
            updated_at = strftime('%Y-%m-%dT%H:%M:%f','now')
         WHERE name = ?10",
        params![
            input.role,
            input.org,
            input.category.as_str(),
            input.model_tier,
            input.max_tokens,
            input.hourly_budget,
            caps_json,
            input.prompt_ref,
            input.escalation_target,
            name,
        ],
    )?;
    Ok(n > 0)
}

/// Delete an agent by name.
pub fn delete_agent(conn: &Connection, name: &str) -> rusqlite::Result<bool> {
    let n = conn.execute("DELETE FROM agent_catalog WHERE name = ?1", params![name])?;
    Ok(n > 0)
}

/// Count active agents (for health check).
pub fn count_active(conn: &Connection) -> rusqlite::Result<u64> {
    let c: i64 = conn.query_row(
        "SELECT COUNT(*) FROM agent_catalog WHERE status = 'active'",
        [],
        |r| r.get(0),
    )?;
    Ok(c as u64)
}

fn row_to_agent(row: &rusqlite::Row) -> rusqlite::Result<AgentSpec> {
    let cat_str: String = row.get(4)?;
    let status_str: String = row.get(11)?;
    let caps_str: String = row.get(8)?;
    Ok(AgentSpec {
        id: row.get(0)?,
        name: row.get(1)?,
        role: row.get(2)?,
        org: row.get(3)?,
        category: AgentCategory::parse(&cat_str).unwrap_or(AgentCategory::CoreUtility),
        model_tier: row.get(5)?,
        max_tokens: row.get(6)?,
        hourly_budget: row.get(7)?,
        capabilities: serde_json::from_str(&caps_str).unwrap_or_default(),
        prompt_ref: row.get(9)?,
        escalation_target: row.get(10)?,
        status: AgentStatus::parse(&status_str).unwrap_or(AgentStatus::Active),
        created_at: row.get(12)?,
        updated_at: row.get(13)?,
    })
}

fn uuid_short() -> String {
    uuid::Uuid::new_v4().to_string()[..8].to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "agents", &crate::schema::migrations())
            .unwrap();
        conn
    }

    #[test]
    fn create_and_get() {
        let conn = setup();
        let input = AgentInput {
            name: "elena-compliance".into(),
            role: "Compliance officer".into(),
            org: "convergio".into(),
            category: AgentCategory::ComplianceLegal,
            model_tier: "t3".into(),
            max_tokens: 100_000,
            hourly_budget: 5.0,
            capabilities: vec!["audit".into(), "review".into()],
            prompt_ref: None,
            escalation_target: Some("ali-orchestrator".into()),
        };
        let id = create_agent(&conn, &input).unwrap();
        assert!(id.starts_with("ag-"));
        let agent = get_agent(&conn, "elena-compliance").unwrap();
        assert_eq!(agent.category, AgentCategory::ComplianceLegal);
        assert_eq!(agent.capabilities, vec!["audit", "review"]);
    }

    #[test]
    fn list_with_filter() {
        let conn = setup();
        for (n, cat) in [
            ("alpha-agent", AgentCategory::CoreUtility),
            ("beta-agent", AgentCategory::DesignUx),
        ] {
            let input = AgentInput {
                name: n.into(),
                role: "test".into(),
                org: "convergio".into(),
                category: cat,
                model_tier: "t2".into(),
                max_tokens: 100_000,
                hourly_budget: 0.0,
                capabilities: vec![],
                prompt_ref: None,
                escalation_target: None,
            };
            create_agent(&conn, &input).unwrap();
        }
        let all = list_agents(&conn, &AgentQuery::default()).unwrap();
        assert_eq!(all.len(), 2);
        let filtered = list_agents(
            &conn,
            &AgentQuery {
                category: Some("core_utility".into()),
                ..Default::default()
            },
        )
        .unwrap();
        assert_eq!(filtered.len(), 1);
    }

    #[test]
    fn update_and_delete() {
        let conn = setup();
        let input = AgentInput {
            name: "temp-agent".into(),
            role: "temporary".into(),
            org: "convergio".into(),
            category: AgentCategory::CoreUtility,
            model_tier: "t1".into(),
            max_tokens: 50_000,
            hourly_budget: 1.0,
            capabilities: vec![],
            prompt_ref: None,
            escalation_target: None,
        };
        create_agent(&conn, &input).unwrap();
        let upd = AgentInput {
            role: "updated role".into(),
            ..input.clone()
        };
        assert!(update_agent(&conn, "temp-agent", &upd).unwrap());
        let agent = get_agent(&conn, "temp-agent").unwrap();
        assert_eq!(agent.role, "updated role");
        assert!(delete_agent(&conn, "temp-agent").unwrap());
        assert!(get_agent(&conn, "temp-agent").is_err());
    }
}
