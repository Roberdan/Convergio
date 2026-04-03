// Plan hierarchy: master plans, sub-plans, dependencies, execution modes.
// Project -> Master Plan (is_master=1) -> Plans (parent_plan_id) -> Waves -> Tasks.

use rusqlite::{params, Connection};
use serde::Serialize;

type PlanRow = (
    i64,
    String,
    String,
    i64,
    i64,
    Option<String>,
    Option<String>,
    bool,
    Option<i64>,
);

#[derive(Debug, Clone, Serialize)]
pub struct PlanNode {
    pub id: i64,
    pub name: String,
    pub status: String,
    pub tasks_done: i64,
    pub tasks_total: i64,
    pub depends_on: Option<String>,
    pub execution_mode: Option<String>,
    pub is_master: bool,
    pub children: Vec<PlanNode>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ProjectTree {
    pub project_id: String,
    pub project_name: String,
    pub plans: Vec<PlanNode>,
    pub total_tasks: i64,
    pub done_tasks: i64,
}

pub fn project_plan_tree(conn: &Connection, project_id: &str) -> rusqlite::Result<ProjectTree> {
    let project_name = conn
        .query_row(
            "SELECT name FROM projects WHERE id = ?1",
            params![project_id],
            |r| r.get::<_, String>(0),
        )
        .unwrap_or_else(|_| project_id.to_string());

    let mut stmt = conn.prepare(
        "SELECT id, name, status, tasks_done, tasks_total, \
         depends_on, execution_mode, is_master, parent_plan_id \
         FROM plans WHERE project_id = ?1 AND status != 'cancelled' \
         ORDER BY is_master DESC, id ASC",
    )?;

    let rows: Vec<PlanRow> = stmt
        .query_map(params![project_id], |r| {
            Ok((
                r.get(0)?,
                r.get(1)?,
                r.get(2)?,
                r.get(3)?,
                r.get(4)?,
                r.get(5)?,
                r.get(6)?,
                r.get::<_, i64>(7).map(|v| v != 0)?,
                r.get(8)?,
            ))
        })?
        .filter_map(|r| r.ok())
        .collect();

    let (mut masters, mut orphans) = (Vec::new(), Vec::new());

    for row in &rows {
        if row.7 {
            masters.push(row_to_node(row));
        }
    }

    for row in &rows {
        if row.7 {
            continue;
        }
        let node = row_to_node(row);
        if let Some(parent_id) = row.8 {
            if let Some(master) = masters.iter_mut().find(|m| m.id == parent_id) {
                master.children.push(node);
                continue;
            }
        }
        orphans.push(node);
    }

    masters.extend(orphans);
    let total_tasks: i64 = masters.iter().map(sum_total).sum();
    let done_tasks: i64 = masters.iter().map(sum_done).sum();

    Ok(ProjectTree {
        project_id: project_id.to_string(),
        project_name,
        plans: masters,
        total_tasks,
        done_tasks,
    })
}

pub fn dependencies_met(conn: &Connection, plan_id: i64) -> rusqlite::Result<bool> {
    let depends_on: Option<String> = conn.query_row(
        "SELECT depends_on FROM plans WHERE id = ?1",
        params![plan_id],
        |r| r.get(0),
    )?;

    let Some(deps) = depends_on else {
        return Ok(true);
    };
    if deps.trim().is_empty() {
        return Ok(true);
    }

    for dep_id_str in deps.split(',') {
        let dep_id: i64 = match dep_id_str.trim().parse() {
            Ok(id) => id,
            Err(_) => continue,
        };
        let status: String = conn.query_row(
            "SELECT status FROM plans WHERE id = ?1",
            params![dep_id],
            |r| r.get(0),
        )?;
        if status != "done" && status != "cancelled" {
            return Ok(false);
        }
    }
    Ok(true)
}

pub fn master_rollup(conn: &Connection, master_id: i64) -> rusqlite::Result<(i64, i64, String)> {
    let mut stmt = conn
        .prepare("SELECT status, tasks_done, tasks_total FROM plans WHERE parent_plan_id = ?1")?;
    let children: Vec<(String, i64, i64)> = stmt
        .query_map(params![master_id], |r| {
            Ok((r.get(0)?, r.get(1)?, r.get(2)?))
        })?
        .filter_map(|r| r.ok())
        .collect();

    if children.is_empty() {
        return Ok((0, 0, "todo".to_string()));
    }

    let total: i64 = children.iter().map(|c| c.2).sum();
    let done: i64 = children.iter().map(|c| c.1).sum();

    let status = if children.iter().all(|c| c.0 == "done" || c.0 == "cancelled") {
        "done"
    } else if children
        .iter()
        .any(|c| c.0 == "doing" || c.0 == "in_progress")
    {
        "doing"
    } else if children.iter().any(|c| c.0 == "blocked") {
        "blocked"
    } else {
        "todo"
    };

    Ok((done, total, status.to_string()))
}

fn row_to_node(row: &PlanRow) -> PlanNode {
    PlanNode {
        id: row.0,
        name: row.1.clone(),
        status: row.2.clone(),
        tasks_done: row.3,
        tasks_total: row.4,
        depends_on: row.5.clone(),
        execution_mode: row.6.clone(),
        is_master: row.7,
        children: Vec::new(),
    }
}

fn sum_total(node: &PlanNode) -> i64 {
    node.tasks_total + node.children.iter().map(sum_total).sum::<i64>()
}

fn sum_done(node: &PlanNode) -> i64 {
    node.tasks_done + node.children.iter().map(sum_done).sum::<i64>()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let pc = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&pc).unwrap();
        convergio_db::migration::apply_migrations(
            &pc,
            "orchestrator",
            &crate::schema::migrations(),
        )
        .unwrap();
        // Apply same schema to our direct connection
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        conn
    }

    #[test]
    fn dependencies_met_no_deps() {
        let conn = setup();
        conn.execute(
            "INSERT INTO plans (id, project_id, name) VALUES (1, 'p1', 'plan-a')",
            [],
        )
        .unwrap();
        assert!(dependencies_met(&conn, 1).unwrap());
    }

    #[test]
    fn dependencies_met_blocked() {
        let conn = setup();
        conn.execute_batch(
            "INSERT INTO plans (id, project_id, name, status) VALUES (1, 'p1', 'dep', 'doing');
             INSERT INTO plans (id, project_id, name, depends_on) VALUES (2, 'p1', 'child', '1');",
        )
        .unwrap();
        assert!(!dependencies_met(&conn, 2).unwrap());
    }

    #[test]
    fn dependencies_met_satisfied() {
        let conn = setup();
        conn.execute_batch(
            "INSERT INTO plans (id, project_id, name, status) VALUES (1, 'p1', 'dep', 'done');
             INSERT INTO plans (id, project_id, name, depends_on) VALUES (2, 'p1', 'child', '1');",
        )
        .unwrap();
        assert!(dependencies_met(&conn, 2).unwrap());
    }

    #[test]
    fn master_rollup_empty() {
        let conn = setup();
        let (done, total, status) = master_rollup(&conn, 999).unwrap();
        assert_eq!((done, total), (0, 0));
        assert_eq!(status, "todo");
    }
}
