//! Seed data orchestrator — inserts all 68 agents into the catalog.
//!
//! Split across seed_core, seed_tech, seed_biz, seed_rest to stay under 250 lines.

use rusqlite::Connection;

mod seed_biz;
mod seed_core;
mod seed_rest;
mod seed_tech;

/// Seed all agent definitions. Skips agents that already exist (by name).
pub fn run(conn: &Connection) -> rusqlite::Result<usize> {
    let all = [
        seed_core::agents(),
        seed_tech::agents(),
        seed_biz::agents(),
        seed_rest::agents(),
    ]
    .concat();

    let mut inserted = 0;
    for input in &all {
        let exists: bool = conn.query_row(
            "SELECT COUNT(*) > 0 FROM agent_catalog WHERE name = ?1",
            [&input.name],
            |r| r.get(0),
        )?;
        if !exists {
            crate::store::create_agent(conn, input)?;
            inserted += 1;
        }
    }
    tracing::info!(total = all.len(), inserted, "agent catalog seeded");
    Ok(inserted)
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
    fn seed_inserts_all_agents() {
        let conn = setup();
        let n = run(&conn).unwrap();
        assert!(n >= 68, "expected >=68 agents, got {n}");
    }

    #[test]
    fn seed_is_idempotent() {
        let conn = setup();
        run(&conn).unwrap();
        let n = run(&conn).unwrap();
        assert_eq!(n, 0, "second seed should insert 0");
    }
}
