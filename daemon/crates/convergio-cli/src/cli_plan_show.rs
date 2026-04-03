// Human-readable formatter for `cvg plan show --human`.
// Displays plan overview with wave/task breakdown using status icons.

use serde_json::Value;

/// Status icon for task display.
fn status_icon(status: &str) -> &'static str {
    match status {
        "done" => "\u{2713}",        // check mark
        "in_progress" => "\u{25cf}", // filled circle
        "submitted" => "~",
        "pending" => "\u{2610}", // empty checkbox
        "blocked" => "!",
        "failed" | "error" => "\u{2717}", // cross mark
        "skipped" | "cancelled" => "x",
        _ => " ",
    }
}

/// Truncate a string to `max` chars, appending ellipsis if needed.
fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}...", &s[..max.saturating_sub(3)])
    }
}

/// Print a plan in human-readable format from the /api/plan-db/json response.
pub fn print_plan_human(val: &Value) {
    let plan_name = val["name"].as_str().unwrap_or("?");
    let plan_id = val["id"].as_i64().unwrap_or(0);
    let plan_status = val["status"].as_str().unwrap_or("?");
    let created = val["created_at"].as_str().unwrap_or("");

    // Count tasks from waves array
    let waves = val["waves"].as_array();
    let (total, done, wave_count) = count_tasks(waves);

    println!("Plan #{plan_id}: {plan_name}");
    println!("Status: {plan_status} | Created: {created}");
    println!("Progress: {done}/{total} tasks ({wave_count} waves)");
    println!("{}", "-".repeat(60));

    if let Some(waves) = waves {
        for (i, wave) in waves.iter().enumerate() {
            print_wave(i + 1, wave);
        }
    }
}

fn count_tasks(waves: Option<&Vec<Value>>) -> (i64, i64, usize) {
    let Some(waves) = waves else {
        return (0, 0, 0);
    };
    let mut total = 0i64;
    let mut done = 0i64;
    for wave in waves {
        if let Some(tasks) = wave["tasks"].as_array() {
            total += tasks.len() as i64;
            done += tasks
                .iter()
                .filter(|t| t["status"].as_str() == Some("done"))
                .count() as i64;
        }
    }
    (total, done, waves.len())
}

fn wave_status(wave: &Value) -> &str {
    // Derive from wave-level field or infer from tasks
    if let Some(s) = wave["status"].as_str() {
        return s;
    }
    let Some(tasks) = wave["tasks"].as_array() else {
        return "pending";
    };
    let all_done = tasks.iter().all(|t| t["status"].as_str() == Some("done"));
    let any_active = tasks.iter().any(|t| {
        matches!(
            t["status"].as_str(),
            Some("in_progress") | Some("submitted")
        )
    });
    if all_done {
        "done"
    } else if any_active {
        "doing"
    } else {
        "pending"
    }
}

fn print_wave(index: usize, wave: &Value) {
    let wave_name = wave["name"]
        .as_str()
        .or_else(|| wave["wave_id"].as_str())
        .unwrap_or("unnamed");
    let ws = wave_status(wave);
    println!("\nWave {index}: {wave_name} [{ws}]");

    let Some(tasks) = wave["tasks"].as_array() else {
        return;
    };
    for task in tasks {
        let tid = task["task_id"]
            .as_str()
            .unwrap_or_else(|| task["id"].as_str().unwrap_or("?"));
        let title = task["title"].as_str().unwrap_or("untitled");
        let status = task["status"].as_str().unwrap_or("pending");
        let model = task["model"].as_str().unwrap_or("");
        let effort = task["effort"].as_i64();
        let icon = status_icon(status);
        let title_trunc = truncate(title, 35);

        let mut suffix = String::new();
        if !model.is_empty() {
            suffix.push_str(&format!("  {model}"));
        }
        if let Some(e) = effort {
            suffix.push_str(&format!("  effort:{e}"));
        }
        println!("  {icon} {tid:<8} {title_trunc:<37}{suffix}");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn status_icons_are_correct() {
        assert_eq!(status_icon("done"), "\u{2713}");
        assert_eq!(status_icon("in_progress"), "\u{25cf}");
        assert_eq!(status_icon("pending"), "\u{2610}");
        assert_eq!(status_icon("failed"), "\u{2717}");
    }

    #[test]
    fn truncate_short_string_unchanged() {
        assert_eq!(truncate("hello", 35), "hello");
    }

    #[test]
    fn truncate_long_string_adds_ellipsis() {
        let long = "a]".repeat(20);
        let result = truncate(&long, 10);
        assert!(result.len() <= 10);
        assert!(result.ends_with("..."));
    }

    #[test]
    fn print_plan_human_no_panic() {
        let plan = json!({
            "id": 10038,
            "name": "Jarvis Fallback Fix + Mesh Auto-Update",
            "status": "doing",
            "created_at": "01 Apr 2026, 09:47 CET",
            "waves": [
                {
                    "name": "Jarvis Fallback",
                    "status": "done",
                    "tasks": [
                        {
                            "task_id": "W1-T1",
                            "title": "Fix keyword fallback",
                            "status": "done",
                            "model": "sonnet",
                            "effort": 1
                        }
                    ]
                },
                {
                    "name": "Mesh Auto-Update",
                    "tasks": [
                        {
                            "task_id": "W2-T1",
                            "title": "Version in heartbeat",
                            "status": "done",
                            "model": "opus",
                            "effort": 2
                        },
                        {
                            "task_id": "W2-T2",
                            "title": "Auto-update loop",
                            "status": "in_progress",
                            "model": "opus",
                            "effort": 3
                        },
                        {
                            "task_id": "W2-T3",
                            "title": "Restart loop + rollback",
                            "status": "pending",
                            "model": "sonnet",
                            "effort": 1
                        }
                    ]
                }
            ]
        });
        // Must not panic
        print_plan_human(&plan);
    }

    #[test]
    fn empty_plan_no_panic() {
        let plan = json!({"id": 1, "name": "empty", "status": "pending"});
        print_plan_human(&plan);
    }

    #[test]
    fn wave_status_inferred_from_tasks() {
        let wave = json!({
            "tasks": [
                {"status": "done"},
                {"status": "done"}
            ]
        });
        assert_eq!(wave_status(&wave), "done");

        let wave2 = json!({
            "tasks": [
                {"status": "done"},
                {"status": "in_progress"}
            ]
        });
        assert_eq!(wave_status(&wave2), "doing");
    }
}
