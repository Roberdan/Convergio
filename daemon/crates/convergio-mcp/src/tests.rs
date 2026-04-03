//! Tests for ring enforcement and tool registry.

use crate::ring::{check_ring_access, McpError, Ring};
use crate::tools::{all_tools, list_tools};

// ── Ring access ──────────────────────────────────────────────────────────────

#[test]
fn ring_core_can_access_all() {
    assert!(check_ring_access(Ring::Core, Ring::Core).is_ok());
    assert!(check_ring_access(Ring::Core, Ring::Trusted).is_ok());
    assert!(check_ring_access(Ring::Core, Ring::Community).is_ok());
    assert!(check_ring_access(Ring::Core, Ring::Sandboxed).is_ok());
}

#[test]
fn ring_trusted_cannot_access_core() {
    assert!(check_ring_access(Ring::Trusted, Ring::Core).is_err());
    assert!(check_ring_access(Ring::Trusted, Ring::Trusted).is_ok());
    assert!(check_ring_access(Ring::Trusted, Ring::Community).is_ok());
}

#[test]
fn ring_community_cannot_access_trusted() {
    assert!(check_ring_access(Ring::Community, Ring::Core).is_err());
    assert!(check_ring_access(Ring::Community, Ring::Trusted).is_err());
    assert!(check_ring_access(Ring::Community, Ring::Community).is_ok());
    assert!(check_ring_access(Ring::Community, Ring::Sandboxed).is_ok());
}

#[test]
fn ring_sandboxed_only_sandboxed() {
    assert!(check_ring_access(Ring::Sandboxed, Ring::Core).is_err());
    assert!(check_ring_access(Ring::Sandboxed, Ring::Trusted).is_err());
    assert!(check_ring_access(Ring::Sandboxed, Ring::Community).is_err());
    assert!(check_ring_access(Ring::Sandboxed, Ring::Sandboxed).is_ok());
}

#[test]
fn ring_violation_error_contains_levels() {
    let err = check_ring_access(Ring::Community, Ring::Trusted).unwrap_err();
    match err {
        McpError::RingViolation { caller, required } => {
            assert_eq!(caller, 2);
            assert_eq!(required, 1);
        }
        _ => panic!("expected RingViolation, got {err:?}"),
    }
}

#[test]
fn ring_default_is_sandboxed() {
    assert_eq!(Ring::default(), Ring::Sandboxed);
}

#[test]
fn ring_from_u8_overflow_becomes_sandboxed() {
    assert_eq!(Ring::from_u8(255), Ring::Sandboxed);
}

// ── Tool registry ────────────────────────────────────────────────────────────

#[test]
fn all_tools_count() {
    let tools = all_tools();
    assert_eq!(tools.len(), 15, "expected 15 tools, got {}", tools.len());
}

#[test]
fn list_tools_core_returns_all() {
    let tools = list_tools(Ring::Core);
    assert_eq!(tools.len(), 15);
}

#[test]
fn list_tools_trusted_excludes_core_only() {
    let tools = list_tools(Ring::Trusted);
    let names: Vec<&str> = tools.iter().map(|t| t.name).collect();
    assert!(!names.contains(&"cvg_restart_node"));
    assert_eq!(tools.len(), 14);
}

#[test]
fn list_tools_community_excludes_write_tools() {
    let tools = list_tools(Ring::Community);
    let names: Vec<&str> = tools.iter().map(|t| t.name).collect();
    assert!(!names.contains(&"cvg_update_task"));
    assert!(!names.contains(&"cvg_checkpoint_save"));
    assert!(!names.contains(&"cvg_agent_start"));
    assert!(!names.contains(&"cvg_restart_node"));
    assert!(names.contains(&"cvg_get_plan"));
}

#[test]
fn list_tools_sandboxed_minimal() {
    let tools = list_tools(Ring::Sandboxed);
    let names: Vec<&str> = tools.iter().map(|t| t.name).collect();
    assert!(names.contains(&"cvg_list_plans"));
    assert!(names.contains(&"cvg_list_agents"));
    assert!(!names.contains(&"cvg_notify"));
    assert_eq!(tools.len(), 2);
}

#[test]
fn all_tools_have_valid_schema() {
    for tool in &all_tools() {
        assert!(!tool.name.is_empty());
        assert!(!tool.description.is_empty());
        assert_eq!(
            tool.input_schema.get("type").and_then(|v| v.as_str()),
            Some("object"),
            "tool {} schema must have type:object",
            tool.name
        );
    }
}

#[test]
fn all_tool_names_use_cvg_prefix() {
    for tool in &all_tools() {
        assert!(
            tool.name.starts_with("cvg_"),
            "tool '{}' must start with cvg_",
            tool.name
        );
    }
}

// ── McpError display ─────────────────────────────────────────────────────────

#[test]
fn mcp_error_display() {
    let e = McpError::DaemonUnreachable;
    assert!(e.to_string().contains("unreachable"));

    let e = McpError::InvalidParams("test");
    assert!(e.to_string().contains("test"));

    let e = McpError::DaemonError("bad".into());
    assert_eq!(e.json_rpc_code(), -32003);
}

#[test]
fn mcp_error_ring_violation_code() {
    let e = McpError::RingViolation {
        caller: 3,
        required: 0,
    };
    assert_eq!(e.json_rpc_code(), -32001);
    assert!(e.message().contains("3"));
    assert!(e.message().contains("0"));
}
