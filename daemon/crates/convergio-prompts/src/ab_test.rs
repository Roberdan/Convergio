//! A/B testing for prompts — run the same task with different prompts, compare.

use rusqlite::{params, Connection};

use crate::types::AbTestResult;

/// Create an A/B test entry.
pub fn create_test(
    conn: &Connection,
    prompt_a_id: &str,
    prompt_b_id: &str,
    task_ref: &str,
) -> rusqlite::Result<String> {
    let test_id = format!("ab-{}", uuid_short());
    conn.execute(
        "INSERT INTO prompt_ab_tests (test_id, prompt_a_id, prompt_b_id, task_ref)
         VALUES (?1, ?2, ?3, ?4)",
        params![test_id, prompt_a_id, prompt_b_id, task_ref],
    )?;
    Ok(test_id)
}

/// Record results for variant A.
pub fn record_variant_a(
    conn: &Connection,
    test_id: &str,
    tokens: u64,
    score: f64,
) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE prompt_ab_tests SET tokens_a = ?1, score_a = ?2 WHERE test_id = ?3",
        params![tokens, score, test_id],
    )?;
    Ok(())
}

/// Record results for variant B.
pub fn record_variant_b(
    conn: &Connection,
    test_id: &str,
    tokens: u64,
    score: f64,
) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE prompt_ab_tests SET tokens_b = ?1, score_b = ?2 WHERE test_id = ?3",
        params![tokens, score, test_id],
    )?;
    Ok(())
}

/// Declare a winner for the test.
pub fn declare_winner(conn: &Connection, test_id: &str, winner: &str) -> rusqlite::Result<()> {
    conn.execute(
        "UPDATE prompt_ab_tests SET winner = ?1 WHERE test_id = ?2",
        params![winner, test_id],
    )?;
    Ok(())
}

/// Get a test result by ID.
pub fn get_test(conn: &Connection, test_id: &str) -> rusqlite::Result<AbTestResult> {
    conn.query_row(
        "SELECT test_id, prompt_a_id, prompt_b_id, task_ref, winner,
                tokens_a, tokens_b, score_a, score_b, created_at
         FROM prompt_ab_tests WHERE test_id = ?1",
        params![test_id],
        row_to_ab_result,
    )
}

/// List all tests for a given task reference.
pub fn list_tests_for_task(
    conn: &Connection,
    task_ref: &str,
) -> rusqlite::Result<Vec<AbTestResult>> {
    let mut stmt = conn.prepare(
        "SELECT test_id, prompt_a_id, prompt_b_id, task_ref, winner,
                tokens_a, tokens_b, score_a, score_b, created_at
         FROM prompt_ab_tests WHERE task_ref = ?1 ORDER BY created_at DESC",
    )?;
    let rows = stmt.query_map(params![task_ref], row_to_ab_result)?;
    rows.collect()
}

fn row_to_ab_result(row: &rusqlite::Row) -> rusqlite::Result<AbTestResult> {
    Ok(AbTestResult {
        test_id: row.get(0)?,
        prompt_a_id: row.get(1)?,
        prompt_b_id: row.get(2)?,
        task_ref: row.get(3)?,
        winner: row.get(4)?,
        tokens_a: row.get::<_, i64>(5)? as u64,
        tokens_b: row.get::<_, i64>(6)? as u64,
        score_a: row.get(7)?,
        score_b: row.get(8)?,
        created_at: row.get(9)?,
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
        // Insert prompt templates so FKs pass.
        conn.execute(
            "INSERT INTO prompt_templates (id, name, version, body) VALUES ('pa', 'a', 1, 'A')",
            [],
        )
        .unwrap();
        conn.execute(
            "INSERT INTO prompt_templates (id, name, version, body) VALUES ('pb', 'b', 1, 'B')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn full_ab_lifecycle() {
        let conn = setup();
        let tid = create_test(&conn, "pa", "pb", "task-42").unwrap();
        record_variant_a(&conn, &tid, 500, 0.85).unwrap();
        record_variant_b(&conn, &tid, 350, 0.90).unwrap();
        declare_winner(&conn, &tid, "pb").unwrap();
        let result = get_test(&conn, &tid).unwrap();
        assert_eq!(result.winner.as_deref(), Some("pb"));
        assert_eq!(result.tokens_a, 500);
        assert_eq!(result.tokens_b, 350);
    }

    #[test]
    fn list_tests_by_task() {
        let conn = setup();
        create_test(&conn, "pa", "pb", "task-99").unwrap();
        create_test(&conn, "pa", "pb", "task-99").unwrap();
        create_test(&conn, "pa", "pb", "task-other").unwrap();
        let results = list_tests_for_task(&conn, "task-99").unwrap();
        assert_eq!(results.len(), 2);
    }
}
