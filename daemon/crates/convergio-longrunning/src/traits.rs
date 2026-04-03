//! LongRunnable trait — the contract for long-running executions.
//!
//! Any execution that can last hours/days implements this trait
//! to participate in heartbeat monitoring, checkpointing, and budget tracking.

use std::time::Duration;

use serde_json::Value;

use crate::types::{ExecutionStage, ProgressSnapshot};

/// The contract for long-running executions in Convergio.
///
/// Implementors get automatic heartbeat monitoring, checkpoint persistence,
/// budget enforcement, and progress streaming via SSE.
pub trait LongRunnable: Send + Sync {
    /// Unique identifier for this execution.
    fn execution_id(&self) -> &str;

    /// How often the monitor should expect a heartbeat.
    /// If no heartbeat arrives within 3x this interval, the reaper kills it.
    fn heartbeat_interval(&self) -> Duration {
        Duration::from_secs(30)
    }

    /// Save current state for later resume. Called periodically and before pause.
    fn checkpoint(&self) -> Value {
        Value::Null
    }

    /// Resume from a previously saved checkpoint.
    fn resume(&mut self, _state: Value) {
        // Default: no-op (stateless execution)
    }

    /// Current progress snapshot for SSE streaming.
    fn progress(&self) -> ProgressSnapshot {
        ProgressSnapshot {
            execution_id: self.execution_id().to_string(),
            percent: 0.0,
            stage: ExecutionStage::Running,
            cost_usd: 0.0,
            eta_secs: None,
            message: None,
        }
    }

    /// Budget limit in USD. None = unlimited.
    fn budget_limit_usd(&self) -> Option<f64> {
        None
    }

    /// Deadline (ISO 8601). None = no deadline.
    fn deadline(&self) -> Option<String> {
        None
    }

    /// Parent execution ID for delegation chains.
    fn parent_execution_id(&self) -> Option<&str> {
        None
    }

    /// Agent name running this execution.
    fn agent_name(&self) -> &str;

    /// Node where this execution is running.
    fn node_name(&self) -> &str;
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestExec {
        id: String,
    }

    impl LongRunnable for TestExec {
        fn execution_id(&self) -> &str {
            &self.id
        }
        fn agent_name(&self) -> &str {
            "test-agent"
        }
        fn node_name(&self) -> &str {
            "test-node"
        }
    }

    #[test]
    fn default_heartbeat_interval() {
        let exec = TestExec { id: "e1".into() };
        assert_eq!(exec.heartbeat_interval(), Duration::from_secs(30));
    }

    #[test]
    fn default_checkpoint_is_null() {
        let exec = TestExec { id: "e2".into() };
        assert_eq!(exec.checkpoint(), Value::Null);
    }

    #[test]
    fn default_budget_is_none() {
        let exec = TestExec { id: "e3".into() };
        assert!(exec.budget_limit_usd().is_none());
    }

    #[test]
    fn default_progress() {
        let exec = TestExec { id: "e4".into() };
        let p = exec.progress();
        assert_eq!(p.execution_id, "e4");
        assert_eq!(p.percent, 0.0);
        assert_eq!(p.stage, ExecutionStage::Running);
    }
}
