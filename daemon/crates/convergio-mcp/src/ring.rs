//! Ring-based access control for MCP tool calls.
//!
//! Lower ring number = more privilege.
//! 0 = Core, 1 = Trusted, 2 = Community, 3 = Sandboxed.

use crate::protocol::error_codes;

// ── Ring ─────────────────────────────────────────────────────────────────────

/// Security ring level. Core is most privileged.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub enum Ring {
    Core = 0,
    Trusted = 1,
    Community = 2,
    #[default]
    Sandboxed = 3,
}

impl Ring {
    /// Parse from u8. Values > 3 become Sandboxed.
    pub fn from_u8(v: u8) -> Self {
        match v {
            0 => Self::Core,
            1 => Self::Trusted,
            2 => Self::Community,
            _ => Self::Sandboxed,
        }
    }

    pub fn as_u8(self) -> u8 {
        self as u8
    }

    /// Returns true if this ring can access a tool at `required` ring level.
    /// Core(0) can access everything; Sandboxed(3) only Sandboxed tools.
    pub fn can_access(self, required: Ring) -> bool {
        (self as u8) <= (required as u8)
    }
}

// ── Error type ───────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum McpError {
    /// Caller ring lacks privilege for the tool.
    RingViolation { caller: u8, required: u8 },
    /// Required parameter absent or wrong type.
    InvalidParams(&'static str),
    /// Daemon HTTP endpoint returned a non-2xx status.
    DaemonError(String),
    /// Daemon TCP connection refused or timed out.
    DaemonUnreachable,
}

impl McpError {
    pub fn json_rpc_code(&self) -> i32 {
        match self {
            Self::RingViolation { .. } => error_codes::RING_VIOLATION,
            Self::InvalidParams(_) => error_codes::INVALID_PARAMS,
            Self::DaemonError(_) => error_codes::DAEMON_ERROR,
            Self::DaemonUnreachable => error_codes::DAEMON_UNREACHABLE,
        }
    }

    pub fn message(&self) -> String {
        match self {
            Self::RingViolation { caller, required } => {
                format!(
                    "Ring violation: caller ring {caller} cannot access \
                     tool requiring ring {required}"
                )
            }
            Self::InvalidParams(msg) => format!("Invalid params: {msg}"),
            Self::DaemonError(msg) => format!("Daemon error: {msg}"),
            Self::DaemonUnreachable => "Daemon unreachable. Is the daemon running?".to_string(),
        }
    }
}

impl std::fmt::Display for McpError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.message())
    }
}

impl std::error::Error for McpError {}

// ── Access check ─────────────────────────────────────────────────────────────

/// Returns Ok if `caller` ring can access a tool at `required` ring level.
pub fn check_ring_access(caller: Ring, required: Ring) -> Result<(), McpError> {
    if caller.can_access(required) {
        Ok(())
    } else {
        Err(McpError::RingViolation {
            caller: caller.as_u8(),
            required: required.as_u8(),
        })
    }
}
