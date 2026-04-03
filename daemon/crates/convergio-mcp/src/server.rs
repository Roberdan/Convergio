//! McpServer: stdio loop + JSON-RPC dispatch.
//!
//! CRITICAL: stdout is protocol-only. All logs go to stderr via tracing.

use std::io::{BufRead, BufReader, Write};

use serde_json::{json, Value};
use tracing::warn;

use crate::handlers::handle_tool_call;
use crate::protocol::{error_codes, JsonRpcRequest, JsonRpcResponse};
use crate::ring::{check_ring_access, Ring};
use crate::tools::list_tools;

// ── Server ───────────────────────────────────────────────────────────────────

pub struct McpServer {
    ring: Ring,
    daemon_url: String,
    api_token: Option<String>,
}

impl McpServer {
    pub fn new(ring_level: u8, daemon_url: &str, token: Option<&str>) -> Self {
        Self {
            ring: Ring::from_u8(ring_level),
            daemon_url: daemon_url.to_string(),
            api_token: token.map(|t| t.to_string()),
        }
    }

    /// Blocking stdio loop: reads JSON-RPC lines from stdin, writes
    /// responses to stdout. Returns when stdin is closed.
    pub fn run_stdio(&self) {
        let stdin = std::io::stdin();
        let stdout = std::io::stdout();
        let reader = BufReader::new(stdin.lock());

        for line in reader.lines() {
            let line = match line {
                Ok(l) => l,
                Err(e) => {
                    eprintln!("stdin read error: {e}");
                    break;
                }
            };
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            let response = self.handle_request(trimmed);
            let mut out = stdout.lock();
            if let Err(e) = writeln!(out, "{response}") {
                eprintln!("stdout write error: {e}");
                break;
            }
            let _ = out.flush();
        }
    }

    /// Parse one JSON-RPC line and return the serialised response.
    /// Never panics — all errors become JSON-RPC error responses.
    pub fn handle_request(&self, raw: &str) -> String {
        let req: JsonRpcRequest = match serde_json::from_str(raw) {
            Ok(r) => r,
            Err(_) => {
                let resp = JsonRpcResponse::error(
                    json!(null),
                    error_codes::INVALID_REQUEST,
                    "Invalid JSON-RPC request",
                );
                return serde_json::to_string(&resp).unwrap_or_default();
            }
        };

        let id = req.id.clone().unwrap_or(json!(null));

        let resp = match req.method.as_str() {
            "initialize" => self.handle_initialize(id),
            "tools/list" => self.handle_tools_list(id),
            "tools/call" => self.handle_tools_call(id, req.params.unwrap_or(json!({}))),
            _ => {
                warn!(method = %req.method, "method not found");
                JsonRpcResponse::error(id, error_codes::METHOD_NOT_FOUND, "Method not found")
            }
        };

        serde_json::to_string(&resp).unwrap_or_default()
    }

    // ── Handlers ─────────────────────────────────────────────────────────────

    fn handle_initialize(&self, id: Value) -> JsonRpcResponse {
        JsonRpcResponse::success(
            id,
            json!({
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "convergio-mcp-server",
                    "version": env!("CARGO_PKG_VERSION")
                }
            }),
        )
    }

    fn handle_tools_list(&self, id: Value) -> JsonRpcResponse {
        let tools: Vec<Value> = list_tools(self.ring)
            .into_iter()
            .map(|t| {
                json!({
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.input_schema,
                })
            })
            .collect();
        JsonRpcResponse::success(id, json!({"tools": tools}))
    }

    fn handle_tools_call(&self, id: Value, params: Value) -> JsonRpcResponse {
        let name = match params.get("name").and_then(|v| v.as_str()) {
            Some(n) => n,
            None => {
                return JsonRpcResponse::error(
                    id,
                    error_codes::INVALID_PARAMS,
                    "tools/call requires params.name",
                );
            }
        };
        let args = params.get("arguments").cloned().unwrap_or(json!({}));

        // Ring access enforcement
        let tool_ring = min_ring_for_tool(name);
        if let Err(e) = check_ring_access(self.ring, tool_ring) {
            return JsonRpcResponse::error(id, e.json_rpc_code(), e.message());
        }

        match handle_tool_call(name, &args, &self.daemon_url, self.api_token.as_deref()) {
            Ok(result) => {
                let text = serde_json::to_string(&result).unwrap_or_else(|_| "{}".to_string());
                JsonRpcResponse::success(
                    id,
                    json!({
                        "content": [{"type": "text", "text": text}]
                    }),
                )
            }
            Err(e) => JsonRpcResponse::error(id, e.json_rpc_code(), e.message()),
        }
    }
}

// ── Ring map ─────────────────────────────────────────────────────────────────

/// Minimum ring required to invoke a named tool.
/// Unknown tools default to Core (most restrictive) to fail-safe.
fn min_ring_for_tool(name: &str) -> Ring {
    match name {
        "cvg_restart_node" => Ring::Core,
        "cvg_update_task"
        | "cvg_checkpoint_save"
        | "cvg_agent_start"
        | "cvg_agent_complete"
        | "cvg_kernel_ask"
        | "cvg_notify"
        | "cvg_interrupt_agent" => Ring::Trusted,
        "cvg_list_plans" | "cvg_list_agents" => Ring::Sandboxed,
        "cvg_get_plan" | "cvg_mesh_status" | "cvg_node_readiness" | "cvg_cost_summary"
        | "cvg_kernel_status" => Ring::Community,
        _ => Ring::Core,
    }
}
