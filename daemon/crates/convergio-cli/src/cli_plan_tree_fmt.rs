// Human-readable formatter for `cvg plan tree --human`.
// Shows plan name, status, and waves with task breakdown.

use serde_json::Value;

pub fn print_execution_tree(val: &Value) {
    let plan = &val["plan"];
    let plan_name = plan["name"].as_str().unwrap_or("?");
    let plan_status = plan["status"].as_str().unwrap_or("?");
    let done = plan["tasks_done"].as_i64().unwrap_or(0);
    let total = plan["tasks_total"].as_i64().unwrap_or(0);

    println!("Plan: {plan_name} [{plan_status}] ({done}/{total} tasks)");
    println!("{}", "-".repeat(70));

    if let Some(tree) = val["tree"].as_array() {
        for entry in tree {
            let wave = &entry["wave"];
            let wave_id = wave["wave_id"].as_str().unwrap_or("?");
            let wave_name = wave["name"].as_str().unwrap_or("unnamed");
            let wave_status = wave["status"].as_str().unwrap_or("?");
            let w_done = wave["tasks_done"].as_i64().unwrap_or(0);
            let w_total = wave["tasks_total"].as_i64().unwrap_or(0);

            println!("\n  {wave_id}: {wave_name} [{wave_status}] ({w_done}/{w_total})");

            if let Some(tasks) = entry["tasks"].as_array() {
                for task in tasks {
                    let tid = task["task_id"].as_str().unwrap_or("?");
                    let title = task["title"].as_str().unwrap_or("untitled");
                    let status = task["status"].as_str().unwrap_or("?");
                    let icon = match status {
                        "done" => "+",
                        "in_progress" => ">",
                        "submitted" => "~",
                        "blocked" => "!",
                        "skipped" | "cancelled" => "x",
                        _ => " ",
                    };
                    println!("    [{icon}] {tid}: {title} ({status})");
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn print_execution_tree_formats_without_panic() {
        let tree = json!({
            "ok": true,
            "plan": {
                "name": "Plan X v2 Hardening",
                "status": "doing",
                "tasks_done": 5,
                "tasks_total": 12,
            },
            "tree": [
                {
                    "wave": {
                        "wave_id": "W1",
                        "name": "Runner Session Fixes",
                        "status": "done",
                        "tasks_done": 3,
                        "tasks_total": 3,
                    },
                    "tasks": [
                        {"task_id": "T1-01", "title": "Fix runner session", "status": "done"},
                        {"task_id": "T1-02", "title": "Add retry logic", "status": "done"},
                    ]
                },
                {
                    "wave": {
                        "wave_id": "W2",
                        "name": "Simple Bug Fixes",
                        "status": "in_progress",
                        "tasks_done": 0,
                        "tasks_total": 4,
                    },
                    "tasks": [
                        {"task_id": "T2-01a", "title": "Fix simple bugs", "status": "in_progress"},
                        {"task_id": "T2-01b", "title": "Fix complex bugs", "status": "pending"},
                    ]
                }
            ]
        });
        // Smoke test: must not panic
        print_execution_tree(&tree);
    }

    #[test]
    fn empty_tree_does_not_panic() {
        let tree = json!({"plan": {}, "tree": []});
        print_execution_tree(&tree);
    }
}
