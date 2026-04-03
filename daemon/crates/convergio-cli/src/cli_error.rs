// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Structured error type for CLI subcommands — replaces direct CLI termination calls.

#[derive(Debug, thiserror::Error)]
pub enum CliError {
    #[error("{0}")]
    InvalidInput(String),
    #[error("{0}")]
    ApiCallFailed(String),
    #[error("{0}")]
    NotFound(String),
    #[error("{0}")]
    ValidationRejected(String),
    #[error("{0}")]
    ViolationsFound(String),
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
}

impl CliError {
    pub fn exit_code(&self) -> i32 {
        match self {
            CliError::NotFound(_)
            | CliError::ValidationRejected(_)
            | CliError::ViolationsFound(_) => 1,
            _ => 2,
        }
    }
}
