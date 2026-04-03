//! MCP tool registry: definitions + ring-filtered listing.
//!
//! Each tool maps to a daemon API endpoint. The catalog defines
//! name, description, JSON Schema, and minimum ring.

use serde_json::{json, Value};

use crate::ring::Ring;

// ── Tool definition ──────────────────────────────────────────────────────────

pub struct McpTool {
    pub name: &'static str,
    pub description: &'static str,
    pub input_schema: Value,
    pub min_ring: Ring,
}

/// Returns all tools visible to `caller_ring`.
pub fn list_tools(caller_ring: Ring) -> Vec<McpTool> {
    all_tools()
        .into_iter()
        .filter(|t| caller_ring.can_access(t.min_ring))
        .collect()
}

/// Full tool catalogue (unfiltered).
pub fn all_tools() -> Vec<McpTool> {
    let mut tools = Vec::with_capacity(20);
    tools.extend(plan_tools());
    tools.extend(agent_tools());
    tools.extend(mesh_tools());
    tools.extend(kernel_tools());
    tools.extend(action_tools());
    tools
}

// ── Plan tools ───────────────────────────────────────────────────────────────

fn plan_tools() -> Vec<McpTool> {
    vec![
        McpTool {
            name: "cvg_list_plans",
            description: "List all plans with optional status filter.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "status_filter": {
                        "type": "string",
                        "description": "Filter by status (pending/doing/done)"
                    }
                }
            }),
            min_ring: Ring::Sandboxed,
        },
        McpTool {
            name: "cvg_get_plan",
            description: "Get full plan details by ID.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "integer",
                        "description": "Plan ID"
                    }
                },
                "required": ["plan_id"]
            }),
            min_ring: Ring::Community,
        },
        McpTool {
            name: "cvg_update_task",
            description: "Update task status and optional summary.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "summary": {"type": "string"}
                },
                "required": ["task_id", "status"]
            }),
            min_ring: Ring::Trusted,
        },
        McpTool {
            name: "cvg_checkpoint_save",
            description: "Save a checkpoint for a plan.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "plan_id": {"type": "integer"}
                },
                "required": ["plan_id"]
            }),
            min_ring: Ring::Trusted,
        },
    ]
}

// ── Agent tools ──────────────────────────────────────────────────────────────

fn agent_tools() -> Vec<McpTool> {
    vec![
        McpTool {
            name: "cvg_list_agents",
            description: "List registered agents with status and last heartbeat.",
            input_schema: json!({"type": "object", "properties": {}}),
            min_ring: Ring::Sandboxed,
        },
        McpTool {
            name: "cvg_agent_start",
            description: "Register an agent as active.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Agent name"},
                    "task_id": {"type": "integer", "description": "Associated task (optional)"}
                },
                "required": ["name"]
            }),
            min_ring: Ring::Trusted,
        },
        McpTool {
            name: "cvg_agent_complete",
            description: "Mark an agent as completed.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "exit_reason": {"type": "string"}
                },
                "required": ["name"]
            }),
            min_ring: Ring::Trusted,
        },
    ]
}

// ── Mesh tools ───────────────────────────────────────────────────────────────

fn mesh_tools() -> Vec<McpTool> {
    vec![
        McpTool {
            name: "cvg_mesh_status",
            description: "Get peer topology and active connections.",
            input_schema: json!({"type": "object", "properties": {}}),
            min_ring: Ring::Community,
        },
        McpTool {
            name: "cvg_node_readiness",
            description: "Run node health checks and return readiness report.",
            input_schema: json!({"type": "object", "properties": {}}),
            min_ring: Ring::Community,
        },
        McpTool {
            name: "cvg_cost_summary",
            description: "Get spending overview: total cost, active and total plans.",
            input_schema: json!({"type": "object", "properties": {}}),
            min_ring: Ring::Community,
        },
    ]
}

// ── Kernel tools ─────────────────────────────────────────────────────────────

fn kernel_tools() -> Vec<McpTool> {
    vec![
        McpTool {
            name: "cvg_kernel_status",
            description: "Get kernel status: models loaded, uptime.",
            input_schema: json!({"type": "object", "properties": {}}),
            min_ring: Ring::Community,
        },
        McpTool {
            name: "cvg_kernel_ask",
            description: "Ask the local LLM a question with platform context.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Question for the LLM"}
                },
                "required": ["prompt"]
            }),
            min_ring: Ring::Trusted,
        },
    ]
}

// ── Action tools ─────────────────────────────────────────────────────────────

fn action_tools() -> Vec<McpTool> {
    vec![
        McpTool {
            name: "cvg_notify",
            description: "Send a notification via configured channel.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "title": {"type": "string"},
                    "severity": {"type": "string", "enum": ["info","warning","error"]}
                },
                "required": ["message"]
            }),
            min_ring: Ring::Trusted,
        },
        McpTool {
            name: "cvg_restart_node",
            description: "Trigger recovery for a target node. Core ring only.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target node hostname"}
                },
                "required": ["target"]
            }),
            min_ring: Ring::Core,
        },
        McpTool {
            name: "cvg_interrupt_agent",
            description: "Interrupt a blocked/stalled agent via IPC bus.",
            input_schema: json!({
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["agent_name", "reason"]
            }),
            min_ring: Ring::Trusted,
        },
    ]
}
