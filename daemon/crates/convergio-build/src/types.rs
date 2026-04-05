//! Types and DTOs for the build module.

use serde::{Deserialize, Serialize};

/// Build status lifecycle.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum BuildStatus {
    Queued,
    Building,
    Testing,
    Compiling,
    Succeeded,
    Failed,
    Deployed,
}

impl std::fmt::Display for BuildStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Queued => write!(f, "queued"),
            Self::Building => write!(f, "building"),
            Self::Testing => write!(f, "testing"),
            Self::Compiling => write!(f, "compiling"),
            Self::Succeeded => write!(f, "succeeded"),
            Self::Failed => write!(f, "failed"),
            Self::Deployed => write!(f, "deployed"),
        }
    }
}

impl BuildStatus {
    pub fn parse_status(s: &str) -> Self {
        match s {
            "queued" => Self::Queued,
            "building" => Self::Building,
            "testing" => Self::Testing,
            "compiling" => Self::Compiling,
            "succeeded" => Self::Succeeded,
            "deployed" => Self::Deployed,
            _ => Self::Failed,
        }
    }
}

/// A build record stored in the database.
#[derive(Debug, Clone, Serialize)]
pub struct BuildRecord {
    pub id: String,
    pub status: BuildStatus,
    pub commit_hash: String,
    pub test_count: Option<i64>,
    pub binary_hash: Option<String>,
    pub binary_size: Option<i64>,
    pub started_at: String,
    pub completed_at: Option<String>,
    pub error: Option<String>,
    pub duration_secs: Option<f64>,
}

/// Error type for build operations.
#[derive(Debug, thiserror::Error)]
pub enum BuildError {
    #[error("db: {0}")]
    Db(#[from] rusqlite::Error),
    #[error("pool: {0}")]
    Pool(String),
    #[error("io: {0}")]
    Io(#[from] std::io::Error),
    #[error("build failed: {0}")]
    BuildFailed(String),
    #[error("deploy failed: {0}")]
    DeployFailed(String),
    #[error("not found: {0}")]
    NotFound(String),
}

pub type BuildResult<T> = std::result::Result<T, BuildError>;
