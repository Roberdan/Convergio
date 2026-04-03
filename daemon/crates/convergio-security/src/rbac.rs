//! Route-level RBAC for agent roles.

use crate::jwt::AgentRole;

/// Check if a role is allowed to access the given route path.
pub fn role_can_access(role: &AgentRole, path: &str) -> bool {
    match role {
        AgentRole::Coordinator => true,
        AgentRole::Dashboard => is_dashboard_route(path),
        AgentRole::Executor => is_executor_route(path),
        AgentRole::Kernel => is_kernel_route(path),
        AgentRole::Worker => is_worker_route(path),
    }
}

fn is_executor_route(path: &str) -> bool {
    path.starts_with("/api/plan-db/task/")
        || path.starts_with("/api/plan-db/agent/")
        || path.starts_with("/api/plan-db/checkpoint/")
        || path.starts_with("/api/plan-db/context/")
        || path.starts_with("/api/plan-db/json/")
        || path.starts_with("/api/plan-db/list")
        || path.starts_with("/api/plan-db/execution-tree/")
        || path.starts_with("/api/plan-db/readiness/")
        || path.starts_with("/api/plan-db/kb")
        || path == "/api/build"
        || path == "/api/test"
        || path.starts_with("/api/build/")
        || path.starts_with("/api/test/")
        || path == "/api/health"
        || path.starts_with("/api/health/")
        || path.starts_with("/api/tracking/")
        || path.starts_with("/api/workspace/")
        || path.starts_with("/api/memory/")
        || path.starts_with("/api/ipc/")
        || path.starts_with("/api/delegate/")
        || path.starts_with("/api/delegation/")
        || path == "/api/notify"
        || path.starts_with("/api/notify/")
}

fn is_kernel_route(path: &str) -> bool {
    path.starts_with("/api/kernel/")
        || path == "/api/notify"
        || path.starts_with("/api/notify/")
        || path == "/api/health"
        || path.starts_with("/api/health/")
        || path.starts_with("/api/node/")
        || path.starts_with("/api/heartbeat")
        || path.starts_with("/api/voice/")
        || path.starts_with("/api/memory/")
}

fn is_worker_route(path: &str) -> bool {
    path.starts_with("/api/plan-db/task/")
        || path.starts_with("/api/plan-db/list")
        || path.starts_with("/api/plan-db/context/")
        || path.starts_with("/api/delegate/status")
        || path.starts_with("/api/delegation/")
        || path == "/api/health"
        || path.starts_with("/api/health/")
        || path.starts_with("/api/heartbeat")
        || path.starts_with("/api/ipc/")
        || path.starts_with("/api/tracking/")
}

fn is_dashboard_route(path: &str) -> bool {
    path == "/api/health"
        || path.starts_with("/api/health/")
        || path.starts_with("/api/overview")
        || path.starts_with("/api/agents")
        || path.starts_with("/api/plans")
        || path.starts_with("/api/plan-db/")
        || path.starts_with("/api/mesh")
        || path.starts_with("/api/tasks/")
        || path.starts_with("/api/notifications")
        || path.starts_with("/api/projects")
        || path.starts_with("/api/events")
        || path.starts_with("/api/peers")
        || path.starts_with("/api/ipc/")
        || path.starts_with("/api/kernel/")
        || path.starts_with("/api/node/")
        || path.starts_with("/api/memory")
        || path.starts_with("/api/audit/")
        || path.starts_with("/ws/")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coordinator_unrestricted() {
        assert!(role_can_access(&AgentRole::Coordinator, "/api/anything"));
    }

    #[test]
    fn executor_can_access_tasks() {
        assert!(role_can_access(&AgentRole::Executor, "/api/plan-db/task/1"));
        assert!(role_can_access(&AgentRole::Executor, "/api/health"));
    }

    #[test]
    fn worker_restricted() {
        assert!(role_can_access(&AgentRole::Worker, "/api/health"));
        assert!(!role_can_access(&AgentRole::Worker, "/api/plan-db/agent/1"));
    }

    #[test]
    fn dashboard_read_only() {
        assert!(role_can_access(&AgentRole::Dashboard, "/api/plans"));
        assert!(!role_can_access(&AgentRole::Dashboard, "/api/build"));
    }
}
