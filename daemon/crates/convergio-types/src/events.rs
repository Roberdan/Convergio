//! Domain events — the heartbeat of the system.
//!
//! Every action, message, and state change is a DomainEvent.
//! Events use human names, not IDs. "Elena", not "agent-7f3a".

use chrono::{DateTime, Utc};

/// Who performed the action.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ActorName {
    /// Human name (e.g. "Elena", "Legal Corp", "convergio-mesh").
    pub name: String,
    /// Organization if applicable.
    pub org: Option<String>,
    /// Node where the actor is running.
    pub node: Option<String>,
}

/// Context for an event — links to plan/task/org if applicable.
#[derive(Debug, Clone, Default, serde::Serialize, serde::Deserialize)]
pub struct EventContext {
    pub org_id: Option<String>,
    pub plan_id: Option<i64>,
    pub task_id: Option<i64>,
}

/// A domain event — streamable via SSE, persistable, subscribable.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DomainEvent {
    pub actor: ActorName,
    pub kind: EventKind,
    pub timestamp: DateTime<Utc>,
    pub context: EventContext,
}

/// Typed event kinds covering orchestration, communication, and system events.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
#[serde(tag = "type")]
pub enum EventKind {
    // Orchestration
    PlanCreated {
        plan_id: i64,
        name: String,
    },
    TaskAssigned {
        task_id: i64,
        agent: String,
        org: String,
    },
    TaskCompleted {
        task_id: i64,
    },

    // Communication (visible in real-time UI)
    MessageSent {
        from: String,
        to: String,
        preview: String,
    },
    DelegationStarted {
        from_org: String,
        to_org: String,
        task: String,
    },

    // Agent lifecycle
    AgentOnline {
        name: String,
        org: String,
        node: String,
    },
    AgentOffline {
        name: String,
        reason: String,
    },

    // System
    HealthDegraded {
        module: String,
        reason: String,
    },
    BudgetAlert {
        org: String,
        spent: f64,
        limit: f64,
    },
    ExtensionLoaded {
        id: String,
        version: String,
    },
}

/// Filter for subscribing to events.
#[derive(Debug, Clone)]
pub struct EventFilter {
    /// Event type prefix (e.g. "Task" matches TaskAssigned, TaskCompleted).
    pub kind_prefix: Option<String>,
    /// Only events from this org.
    pub org: Option<String>,
    /// Only events from this actor.
    pub actor: Option<String>,
}
