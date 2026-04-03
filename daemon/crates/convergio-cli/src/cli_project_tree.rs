// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Tree-view printer for `cvg project plans` — split from cli_project.rs for 250-line limit.

use serde_json::Value;

pub fn print_project_tree(val: &Value, fallback_id: &str) {
    println!(
        "Project: {} ({})",
        val["project_name"].as_str().unwrap_or(fallback_id),
        val["project_id"].as_str().unwrap_or(fallback_id),
    );
    println!(
        "Tasks: {}/{}\n",
        val["done_tasks"].as_i64().unwrap_or(0),
        val["total_tasks"].as_i64().unwrap_or(0),
    );
    if let Some(plans) = val["plans"].as_array() {
        for plan in plans {
            print_plan_node(plan, 0);
        }
    }
}

fn print_plan_node(node: &Value, depth: usize) {
    let indent = "  ".repeat(depth);
    let marker = if node["is_master"].as_bool().unwrap_or(false) { "+" } else { "-" };
    let mode = node["execution_mode"].as_str().unwrap_or("");
    let deps = node["depends_on"].as_str().unwrap_or("");
    println!(
        "{indent}{marker} [{}] {} ({}/{}){}{}",
        node["status"].as_str().unwrap_or("?"),
        node["name"].as_str().unwrap_or("unnamed"),
        node["tasks_done"].as_i64().unwrap_or(0),
        node["tasks_total"].as_i64().unwrap_or(0),
        if mode.is_empty() { String::new() } else { format!(" mode={mode}") },
        if deps.is_empty() { String::new() } else { format!(" depends_on={deps}") },
    );
    if let Some(children) = node["children"].as_array() {
        for child in children {
            print_plan_node(child, depth + 1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn print_project_tree_formats_output() {
        let tree = json!({
            "project_id": "p1",
            "project_name": "TestProject",
            "total_tasks": 10,
            "done_tasks": 6,
            "plans": [
                {
                    "id": 1, "name": "Master", "status": "doing",
                    "tasks_done": 5, "tasks_total": 8, "is_master": true,
                    "execution_mode": "mixed", "depends_on": null,
                    "children": [
                        {
                            "id": 2, "name": "Child A", "status": "done",
                            "tasks_done": 5, "tasks_total": 5, "is_master": false,
                            "execution_mode": null, "depends_on": null, "children": []
                        },
                        {
                            "id": 3, "name": "Child B", "status": "todo",
                            "tasks_done": 0, "tasks_total": 3, "is_master": false,
                            "execution_mode": null, "depends_on": "2", "children": []
                        }
                    ]
                },
                {
                    "id": 4, "name": "Orphan", "status": "doing",
                    "tasks_done": 1, "tasks_total": 2, "is_master": false,
                    "execution_mode": null, "depends_on": null, "children": []
                }
            ]
        });
        // Smoke test: just verify it doesn't panic
        print_project_tree(&tree, "p1");
    }
}
