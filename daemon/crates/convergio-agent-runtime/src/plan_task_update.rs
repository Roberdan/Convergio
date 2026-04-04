/// Update plan task status after agent completion.
/// Reads task_id from art_agents, then calls the plan-db task/update API.
pub fn update_plan_task(pool: &convergio_db::pool::ConnPool, agent_id: &str, status: &str) {
    let task_id: Option<i64> = pool
        .get()
        .ok()
        .and_then(|conn| {
            conn.query_row(
                "SELECT task_id FROM art_agents WHERE id = ?1",
                rusqlite::params![agent_id],
                |row| row.get(0),
            )
            .ok()
        })
        .flatten();

    let Some(task_id) = task_id else {
        tracing::debug!(agent_id, "no task_id linked — skipping plan update");
        return;
    };

    tracing::info!(agent_id, task_id, status, "updating plan task status");

    let body = serde_json::json!({
        "task_id": task_id,
        "status": status,
        "executor_agent": agent_id,
    });

    let status_owned = status.to_string();
    let url = "http://localhost:8420/api/plan-db/task/update";
    tokio::spawn(async move {
        let client = reqwest::Client::new();
        match client.post(url).json(&body).send().await {
            Ok(resp) if resp.status().is_success() => {
                tracing::info!(task_id, status = status_owned.as_str(), "plan task updated");
            }
            Ok(resp) => {
                let text = resp.text().await.unwrap_or_default();
                tracing::warn!(task_id, "plan task update failed: {text}");
            }
            Err(e) => {
                tracing::warn!(task_id, "plan task update HTTP error: {e}");
            }
        }
    });
}
