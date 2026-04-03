//! JSON-RPC 2.0 types for the MCP protocol.
//!
//! stdout is reserved for protocol messages — all logs go to stderr.

use serde::{Deserialize, Serialize};
use serde_json::Value;

// ── Request ──────────────────────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
pub struct JsonRpcRequest {
    pub jsonrpc: String,
    /// Absent for notifications.
    pub id: Option<Value>,
    pub method: String,
    pub params: Option<Value>,
}

// ── Response ─────────────────────────────────────────────────────────────────

/// Serialised to stdout. Only one of result/error is non-null per spec.
#[derive(Debug, Serialize)]
pub struct JsonRpcResponse {
    pub jsonrpc: String,
    pub id: Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<JsonRpcError>,
}

impl JsonRpcResponse {
    pub fn success(id: Value, result: Value) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            result: Some(result),
            error: None,
        }
    }

    pub fn error(id: Value, code: i32, message: impl Into<String>) -> Self {
        Self {
            jsonrpc: "2.0".to_string(),
            id,
            result: None,
            error: Some(JsonRpcError {
                code,
                message: message.into(),
            }),
        }
    }
}

// ── Error ────────────────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
}

/// Standard and custom JSON-RPC error codes.
pub mod error_codes {
    /// Ring access violation — caller ring cannot use this tool.
    pub const RING_VIOLATION: i32 = -32001;
    /// Daemon at configured URL is unreachable.
    pub const DAEMON_UNREACHABLE: i32 = -32002;
    /// Daemon returned a non-2xx status or error body.
    pub const DAEMON_ERROR: i32 = -32003;
    /// Malformed JSON-RPC envelope.
    pub const INVALID_REQUEST: i32 = -32600;
    /// Method name not recognised.
    pub const METHOD_NOT_FOUND: i32 = -32601;
    /// Required parameter missing or wrong type.
    pub const INVALID_PARAMS: i32 = -32602;
}
