//! Token usage tracking and prompt optimization suggestions.

use rusqlite::{params, Connection};

use crate::render::estimate_tokens;
use crate::types::TokenStats;

/// Record token usage for a prompt.
pub fn record_usage(conn: &Connection, prompt_id: &str, tokens: u64) -> rusqlite::Result<()> {
    conn.execute(
        "INSERT INTO prompt_token_usage (prompt_id, tokens) VALUES (?1, ?2)",
        params![prompt_id, tokens],
    )?;
    Ok(())
}

/// Get aggregated token stats for a prompt.
pub fn get_stats(conn: &Connection, prompt_id: &str) -> rusqlite::Result<TokenStats> {
    conn.query_row(
        "SELECT prompt_id, COALESCE(SUM(tokens), 0), COUNT(*), COALESCE(AVG(tokens), 0)
         FROM prompt_token_usage WHERE prompt_id = ?1
         GROUP BY prompt_id",
        params![prompt_id],
        |row| {
            Ok(TokenStats {
                prompt_id: row.get(0)?,
                total_tokens: row.get::<_, i64>(1)? as u64,
                usage_count: row.get::<_, i64>(2)? as u64,
                avg_tokens: row.get(3)?,
            })
        },
    )
}

/// Analyze a prompt body and return optimization suggestions.
pub fn suggest_optimizations(body: &str) -> Vec<String> {
    let mut suggestions = Vec::new();
    let token_count = estimate_tokens(body);

    if token_count > 2000 {
        suggestions.push(format!(
            "Prompt is ~{token_count} tokens. Consider splitting into smaller templates."
        ));
    }
    if body.lines().filter(|l| l.trim().is_empty()).count() > 5 {
        suggestions.push("Excessive blank lines detected. Remove to save tokens.".into());
    }
    // Detect repeated phrases (simple heuristic).
    let words: Vec<&str> = body.split_whitespace().collect();
    if words.len() > 20 {
        let unique = words.iter().collect::<std::collections::HashSet<_>>().len();
        let ratio = unique as f64 / words.len() as f64;
        if ratio < 0.5 {
            suggestions.push(
                "High word repetition detected. Consider using variables or references.".into(),
            );
        }
    }
    suggestions
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "prompts", &crate::schema::migrations())
            .unwrap();
        // Insert a prompt so FK is satisfied.
        conn.execute(
            "INSERT INTO prompt_templates (id, name, version, body) VALUES ('pt-test', 'test', 1, 'body')",
            [],
        )
        .unwrap();
        conn
    }

    #[test]
    fn record_and_get_stats() {
        let conn = setup();
        record_usage(&conn, "pt-test", 100).unwrap();
        record_usage(&conn, "pt-test", 200).unwrap();
        let stats = get_stats(&conn, "pt-test").unwrap();
        assert_eq!(stats.total_tokens, 300);
        assert_eq!(stats.usage_count, 2);
        assert!((stats.avg_tokens - 150.0).abs() < 0.01);
    }

    #[test]
    fn suggest_on_long_prompt() {
        let long_body = "word ".repeat(3000);
        let suggestions = suggest_optimizations(&long_body);
        assert!(!suggestions.is_empty());
        assert!(suggestions[0].contains("tokens"));
    }

    #[test]
    fn no_suggestions_for_short_prompt() {
        let suggestions = suggest_optimizations("You are an engineer.");
        assert!(suggestions.is_empty());
    }
}
