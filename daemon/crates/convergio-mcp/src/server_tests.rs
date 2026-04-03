//! Tests for JSON-RPC protocol parsing and server dispatch.

use serde_json::{json, Value};

use crate::protocol::{JsonRpcRequest, JsonRpcResponse};
use crate::server::McpServer;

// ── Protocol parsing ─────────────────────────────────────────────────────────

#[test]
fn parse_initialize_request() {
    let raw = r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}"#;
    let req: JsonRpcRequest = serde_json::from_str(raw).unwrap();
    assert_eq!(req.method, "initialize");
    assert_eq!(req.id, Some(json!(1)));
}

#[test]
fn parse_tools_list_request() {
    let raw = r#"{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}"#;
    let req: JsonRpcRequest = serde_json::from_str(raw).unwrap();
    assert_eq!(req.method, "tools/list");
}

#[test]
fn parse_tools_call_request() {
    let raw = r#"{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"cvg_list_plans","arguments":{}}}"#;
    let req: JsonRpcRequest = serde_json::from_str(raw).unwrap();
    let params = req.params.unwrap();
    assert_eq!(
        params.get("name").and_then(|v| v.as_str()),
        Some("cvg_list_plans")
    );
}

#[test]
fn parse_malformed_json_fails() {
    let result = serde_json::from_str::<JsonRpcRequest>("not json{{{");
    assert!(result.is_err());
}

// ── Response serialization ───────────────────────────────────────────────────

#[test]
fn response_success_serializes() {
    let resp = JsonRpcResponse::success(json!(1), json!({"ok": true}));
    let v: Value = serde_json::to_value(&resp).unwrap();
    assert_eq!(v.get("jsonrpc").and_then(|v| v.as_str()), Some("2.0"));
    assert!(v.get("result").is_some());
    assert!(v.get("error").is_none());
}

#[test]
fn response_error_serializes() {
    let resp = JsonRpcResponse::error(json!(1), -32601, "Method not found");
    let v: Value = serde_json::to_value(&resp).unwrap();
    assert!(v.get("error").is_some());
    assert!(v.get("result").is_none());
    let err = v.get("error").unwrap();
    assert_eq!(err.get("code").and_then(|v| v.as_i64()), Some(-32601));
}

// ── Server dispatch ──────────────────────────────────────────────────────────

#[test]
fn handle_initialize_returns_server_info() {
    let server = McpServer::new(1, "http://localhost:1", None);
    let raw = r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}"#;
    let resp_str = server.handle_request(raw);
    let v: Value = serde_json::from_str(&resp_str).unwrap();
    let result = v.get("result").expect("must return result");
    assert_eq!(
        result
            .get("serverInfo")
            .and_then(|s| s.get("name"))
            .and_then(|v| v.as_str()),
        Some("convergio-mcp-server")
    );
}

#[test]
fn handle_tools_list_returns_array() {
    let server = McpServer::new(1, "http://localhost:1", None);
    let raw = r#"{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}"#;
    let resp_str = server.handle_request(raw);
    let v: Value = serde_json::from_str(&resp_str).unwrap();
    let tools = v
        .get("result")
        .and_then(|r| r.get("tools"))
        .expect("must return tools");
    assert!(tools.is_array());
    assert_eq!(tools.as_array().unwrap().len(), 14);
}

#[test]
fn handle_unknown_method_returns_error() {
    let server = McpServer::new(1, "http://localhost:1", None);
    let raw = r#"{"jsonrpc":"2.0","id":5,"method":"foo/bar","params":{}}"#;
    let resp_str = server.handle_request(raw);
    let v: Value = serde_json::from_str(&resp_str).unwrap();
    let err = v.get("error").expect("must return error");
    assert_eq!(err.get("code").and_then(|c| c.as_i64()), Some(-32601));
}

#[test]
fn handle_ring_violation_returns_ring_error() {
    let server = McpServer::new(2, "http://localhost:1", None);
    let raw = r#"{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"cvg_update_task","arguments":{"task_id":1,"status":"done"}}}"#;
    let resp_str = server.handle_request(raw);
    let v: Value = serde_json::from_str(&resp_str).unwrap();
    let err = v.get("error").expect("ring violation must return error");
    assert_eq!(err.get("code").and_then(|c| c.as_i64()), Some(-32001));
}

#[test]
fn handle_daemon_unreachable_returns_error() {
    let server = McpServer::new(1, "http://localhost:1", None);
    let raw = r#"{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"cvg_list_plans","arguments":{}}}"#;
    let resp_str = server.handle_request(raw);
    let v: Value = serde_json::from_str(&resp_str).unwrap();
    assert!(
        v.get("error").is_some(),
        "unreachable daemon must return error"
    );
}

#[test]
fn handle_invalid_json_returns_parse_error() {
    let server = McpServer::new(0, "http://localhost:1", None);
    let resp_str = server.handle_request("not valid json");
    let v: Value = serde_json::from_str(&resp_str).unwrap();
    let err = v.get("error").expect("must return error");
    assert_eq!(err.get("code").and_then(|c| c.as_i64()), Some(-32600));
}

#[test]
fn handle_tools_call_missing_name_returns_invalid_params() {
    let server = McpServer::new(0, "http://localhost:1", None);
    let raw = r#"{"jsonrpc":"2.0","id":8,"method":"tools/call","params":{"arguments":{}}}"#;
    let resp_str = server.handle_request(raw);
    let v: Value = serde_json::from_str(&resp_str).unwrap();
    let err = v.get("error").expect("must return error");
    assert_eq!(err.get("code").and_then(|c| c.as_i64()), Some(-32602));
}
