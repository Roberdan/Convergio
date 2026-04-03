//! CRUD operations for prompt templates.

use rusqlite::{params, Connection};

use crate::types::{PromptInput, PromptQuery, PromptTemplate, PromptVariable};

/// Create a new prompt template, returning its ID.
pub fn create_prompt(conn: &Connection, input: &PromptInput) -> rusqlite::Result<String> {
    let id = format!("pt-{}", &uuid_short());
    let vars_json = serde_json::to_string(&input.variables).unwrap_or_default();
    let next_version = next_version_for(conn, &input.name)?;

    // Deactivate previous versions of this prompt name.
    conn.execute(
        "UPDATE prompt_templates SET active = 0 WHERE name = ?1",
        params![input.name],
    )?;

    conn.execute(
        "INSERT INTO prompt_templates (id, name, version, body, variables, category, active)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, 1)",
        params![
            id,
            input.name,
            next_version,
            input.body,
            vars_json,
            input.category
        ],
    )?;
    Ok(id)
}

/// Get a prompt template by ID.
pub fn get_prompt(conn: &Connection, id: &str) -> rusqlite::Result<PromptTemplate> {
    conn.query_row(
        "SELECT id, name, version, body, variables, category, active, created_at, updated_at
         FROM prompt_templates WHERE id = ?1",
        params![id],
        row_to_prompt,
    )
}

/// Get the active version of a prompt by name.
pub fn get_active_prompt(conn: &Connection, name: &str) -> rusqlite::Result<PromptTemplate> {
    conn.query_row(
        "SELECT id, name, version, body, variables, category, active, created_at, updated_at
         FROM prompt_templates WHERE name = ?1 AND active = 1
         ORDER BY version DESC LIMIT 1",
        params![name],
        row_to_prompt,
    )
}

/// List prompts with optional filters.
pub fn list_prompts(
    conn: &Connection,
    query: &PromptQuery,
) -> rusqlite::Result<Vec<PromptTemplate>> {
    let mut sql = String::from(
        "SELECT id, name, version, body, variables, category, active, created_at, updated_at
         FROM prompt_templates WHERE 1=1",
    );
    let mut param_values: Vec<Box<dyn rusqlite::types::ToSql>> = vec![];

    if let Some(ref name) = query.name {
        sql.push_str(&format!(" AND name = ?{}", param_values.len() + 1));
        param_values.push(Box::new(name.clone()));
    }
    if let Some(ref cat) = query.category {
        sql.push_str(&format!(" AND category = ?{}", param_values.len() + 1));
        param_values.push(Box::new(cat.clone()));
    }
    if query.active_only.unwrap_or(false) {
        sql.push_str(" AND active = 1");
    }
    sql.push_str(" ORDER BY name, version DESC");

    let params_ref: Vec<&dyn rusqlite::types::ToSql> =
        param_values.iter().map(|p| p.as_ref()).collect();
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(params_ref.as_slice(), row_to_prompt)?;
    rows.collect()
}

/// Delete a prompt template by ID.
pub fn delete_prompt(conn: &Connection, id: &str) -> rusqlite::Result<bool> {
    let count = conn.execute("DELETE FROM prompt_templates WHERE id = ?1", params![id])?;
    Ok(count > 0)
}

fn next_version_for(conn: &Connection, name: &str) -> rusqlite::Result<u32> {
    let max: Option<u32> = conn
        .query_row(
            "SELECT MAX(version) FROM prompt_templates WHERE name = ?1",
            params![name],
            |r| r.get(0),
        )
        .unwrap_or(None);
    Ok(max.unwrap_or(0) + 1)
}

fn row_to_prompt(row: &rusqlite::Row) -> rusqlite::Result<PromptTemplate> {
    let vars_str: String = row.get(4)?;
    let variables: Vec<PromptVariable> = serde_json::from_str(&vars_str).unwrap_or_default();
    Ok(PromptTemplate {
        id: row.get(0)?,
        name: row.get(1)?,
        version: row.get(2)?,
        body: row.get(3)?,
        variables,
        category: row.get(5)?,
        active: row.get::<_, i32>(6)? != 0,
        created_at: row.get(7)?,
        updated_at: row.get(8)?,
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
        convergio_db::migration::apply_migrations(&conn, "prompts", &crate::schema::migrations())
            .unwrap();
        conn
    }

    #[test]
    fn create_and_get_prompt() {
        let conn = setup();
        let input = PromptInput {
            name: "system-role".into(),
            body: "You are {{role}} for {{org}}.".into(),
            variables: vec![
                PromptVariable {
                    name: "role".into(),
                    description: "Agent role".into(),
                    required: true,
                    default_value: None,
                },
                PromptVariable {
                    name: "org".into(),
                    description: "Organization".into(),
                    required: false,
                    default_value: Some("Convergio".into()),
                },
            ],
            category: Some("system".into()),
        };
        let id = create_prompt(&conn, &input).unwrap();
        let prompt = get_prompt(&conn, &id).unwrap();
        assert_eq!(prompt.name, "system-role");
        assert_eq!(prompt.version, 1);
        assert!(prompt.active);
        assert_eq!(prompt.variables.len(), 2);
    }

    #[test]
    fn versioning_deactivates_old() {
        let conn = setup();
        let input = PromptInput {
            name: "greeting".into(),
            body: "Hello v1".into(),
            variables: vec![],
            category: None,
        };
        let id1 = create_prompt(&conn, &input).unwrap();
        let input2 = PromptInput {
            name: "greeting".into(),
            body: "Hello v2".into(),
            variables: vec![],
            category: None,
        };
        let id2 = create_prompt(&conn, &input2).unwrap();
        let p1 = get_prompt(&conn, &id1).unwrap();
        let p2 = get_prompt(&conn, &id2).unwrap();
        assert!(!p1.active);
        assert!(p2.active);
        assert_eq!(p2.version, 2);
    }

    #[test]
    fn get_active_prompt_returns_latest() {
        let conn = setup();
        for i in 1..=3 {
            let input = PromptInput {
                name: "evolving".into(),
                body: format!("Version {i}"),
                variables: vec![],
                category: None,
            };
            create_prompt(&conn, &input).unwrap();
        }
        let active = get_active_prompt(&conn, "evolving").unwrap();
        assert_eq!(active.version, 3);
        assert_eq!(active.body, "Version 3");
    }

    #[test]
    fn delete_prompt_works() {
        let conn = setup();
        let input = PromptInput {
            name: "disposable".into(),
            body: "bye".into(),
            variables: vec![],
            category: None,
        };
        let id = create_prompt(&conn, &input).unwrap();
        assert!(delete_prompt(&conn, &id).unwrap());
        assert!(get_prompt(&conn, &id).is_err());
    }

    #[test]
    fn list_prompts_with_filters() {
        let conn = setup();
        for name in ["alpha", "beta"] {
            let input = PromptInput {
                name: name.into(),
                body: "test".into(),
                variables: vec![],
                category: Some("system".into()),
            };
            create_prompt(&conn, &input).unwrap();
        }
        let all = list_prompts(&conn, &PromptQuery::default()).unwrap();
        assert_eq!(all.len(), 2);
        let filtered = list_prompts(
            &conn,
            &PromptQuery {
                name: Some("alpha".into()),
                ..Default::default()
            },
        )
        .unwrap();
        assert_eq!(filtered.len(), 1);
    }
}
