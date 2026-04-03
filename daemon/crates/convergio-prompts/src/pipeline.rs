//! CRUD operations for declarative pipelines.

use rusqlite::{params, Connection};

use crate::types::{PipelineDefinition, PipelineInput, PipelineStep};

/// Create a new pipeline, returning its ID.
pub fn create_pipeline(conn: &Connection, input: &PipelineInput) -> rusqlite::Result<String> {
    let id = format!("pl-{}", &uuid_short());
    let steps_json = serde_json::to_string(&input.steps).unwrap_or_default();
    conn.execute(
        "INSERT INTO prompt_pipelines (id, name, description, steps_json, active)
         VALUES (?1, ?2, ?3, ?4, 1)",
        params![id, input.name, input.description, steps_json],
    )?;
    Ok(id)
}

/// Get a pipeline by name.
pub fn get_pipeline(conn: &Connection, name: &str) -> rusqlite::Result<PipelineDefinition> {
    conn.query_row(
        "SELECT id, name, description, steps_json, active, created_at, updated_at
         FROM prompt_pipelines WHERE name = ?1",
        params![name],
        row_to_pipeline,
    )
}

/// List all pipelines.
pub fn list_pipelines(conn: &Connection) -> rusqlite::Result<Vec<PipelineDefinition>> {
    let mut stmt = conn.prepare(
        "SELECT id, name, description, steps_json, active, created_at, updated_at
         FROM prompt_pipelines ORDER BY name",
    )?;
    let rows = stmt.query_map([], row_to_pipeline)?;
    rows.collect()
}

/// Delete a pipeline by name.
pub fn delete_pipeline(conn: &Connection, name: &str) -> rusqlite::Result<bool> {
    let count = conn.execute(
        "DELETE FROM prompt_pipelines WHERE name = ?1",
        params![name],
    )?;
    Ok(count > 0)
}

fn row_to_pipeline(row: &rusqlite::Row) -> rusqlite::Result<PipelineDefinition> {
    let steps_str: String = row.get(3)?;
    let steps: Vec<PipelineStep> = serde_json::from_str(&steps_str).unwrap_or_default();
    Ok(PipelineDefinition {
        id: row.get(0)?,
        name: row.get(1)?,
        description: row.get(2)?,
        steps,
        active: row.get::<_, i32>(4)? != 0,
        created_at: row.get(5)?,
        updated_at: row.get(6)?,
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
    fn create_and_get_pipeline() {
        let conn = setup();
        let input = PipelineInput {
            name: "test-flow".into(),
            description: "A test pipeline".into(),
            steps: vec![
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
            ],
        };
        let id = create_pipeline(&conn, &input).unwrap();
        assert!(id.starts_with("pl-"));
        let got = get_pipeline(&conn, "test-flow").unwrap();
        assert_eq!(got.steps.len(), 2);
        assert_eq!(got.steps[0].skill, "solve");
    }

    #[test]
    fn list_and_delete_pipelines() {
        let conn = setup();
        let input = PipelineInput {
            name: "to-delete".into(),
            description: "temp".into(),
            steps: vec![],
        };
        create_pipeline(&conn, &input).unwrap();
        let all = list_pipelines(&conn).unwrap();
        assert_eq!(all.len(), 1);
        assert!(delete_pipeline(&conn, "to-delete").unwrap());
        assert!(list_pipelines(&conn).unwrap().is_empty());
    }
}
