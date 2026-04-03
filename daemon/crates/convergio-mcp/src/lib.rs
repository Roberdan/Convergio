//! convergio-mcp: MCP server binary for Convergio.
//!
//! Exposes daemon capabilities as MCP tools over JSON-RPC stdio transport.
//! This is a standalone binary that bridges Claude Code/Copilot to the
//! Convergio daemon API via HTTP.

pub mod handlers;
pub mod http;
pub mod protocol;
pub mod ring;
pub mod server;
pub mod tools;

#[cfg(test)]
#[path = "tests.rs"]
mod tests;

#[cfg(test)]
#[path = "server_tests.rs"]
mod server_tests;
