// Core orchestrator types: task status, plan/wave/task views.

use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskStatus {
    Pending,
    InProgress,
    Submitted,
    Done,
    Blocked,
    Skipped,
    Cancelled,
}

impl TaskStatus {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Pending => "pending",
            Self::InProgress => "in_progress",
            Self::Submitted => "submitted",
            Self::Done => "done",
            Self::Blocked => "blocked",
            Self::Skipped => "skipped",
            Self::Cancelled => "cancelled",
        }
    }
}

impl std::str::FromStr for TaskStatus {
    type Err = ();
    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "pending" => Ok(Self::Pending),
            "in_progress" => Ok(Self::InProgress),
            "submitted" => Ok(Self::Submitted),
            "done" => Ok(Self::Done),
            "blocked" => Ok(Self::Blocked),
            "skipped" => Ok(Self::Skipped),
            "cancelled" => Ok(Self::Cancelled),
            _ => Err(()),
        }
    }
}

impl std::fmt::Display for TaskStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ActivePlan {
    pub id: i64,
    pub project_id: String,
    pub name: String,
    pub status: String,
    pub tasks_done: i64,
    pub tasks_total: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct InProgressTask {
    pub id: i64,
    pub project_id: String,
    pub task_id: String,
    pub title: String,
    pub wave_id: String,
}

#[derive(Debug, Clone, Default)]
pub struct UpdateTaskArgs {
    pub notes: Option<String>,
    pub tokens: Option<i64>,
    pub output_data: Option<String>,
    pub executor_host: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct UpdateTaskResult {
    pub old_status: String,
    pub new_status: String,
}

#[derive(Debug, Clone, Default)]
pub struct ValidateTaskArgs {
    pub identifier: String,
    pub plan_id: Option<i64>,
    pub validated_by: String,
    pub force: bool,
    pub report: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ValidateTaskResult {
    pub task_db_id: i64,
    pub task_id: String,
    pub old_status: String,
    pub new_status: String,
    pub validated_by: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ExecutionTaskNode {
    pub id: i64,
    pub task_id: String,
    pub title: String,
    pub status: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ExecutionWaveNode {
    pub id: i64,
    pub wave_id: String,
    pub name: String,
    pub status: String,
    pub tasks_done: i64,
    pub tasks_total: i64,
    pub tasks: Vec<ExecutionTaskNode>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ExecutionTree {
    pub plan_id: i64,
    pub plan_name: String,
    pub plan_status: String,
    pub waves: Vec<ExecutionWaveNode>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn task_status_roundtrip() {
        for s in [
            "pending",
            "in_progress",
            "submitted",
            "done",
            "blocked",
            "skipped",
            "cancelled",
        ] {
            let parsed: TaskStatus = s.parse().unwrap();
            assert_eq!(parsed.as_str(), s);
            assert_eq!(parsed.to_string(), s);
        }
    }

    #[test]
    fn task_status_invalid() {
        assert!("invalid".parse::<TaskStatus>().is_err());
    }
}
