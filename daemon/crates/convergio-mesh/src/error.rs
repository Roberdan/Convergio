//! General mesh error type covering auth, config, db, io, network.

use thiserror::Error;

#[derive(Debug, Error)]
pub enum MeshError {
    #[error("IO error: {0}")]
    Io(String),
    #[error("database error: {0}")]
    Db(String),
    #[error("serialization error: {0}")]
    Serialization(String),
    #[error("config error: {0}")]
    Config(String),
    #[error("network error: {0}")]
    Network(String),
    #[error("auth error: {0}")]
    Auth(String),
    #[error("internal error: {0}")]
    Internal(String),
}

impl From<std::io::Error> for MeshError {
    fn from(e: std::io::Error) -> Self {
        MeshError::Io(e.to_string())
    }
}

impl From<rusqlite::Error> for MeshError {
    fn from(e: rusqlite::Error) -> Self {
        MeshError::Db(e.to_string())
    }
}

impl From<serde_json::Error> for MeshError {
    fn from(e: serde_json::Error) -> Self {
        MeshError::Serialization(e.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn error_display_messages() {
        let e = MeshError::Auth("bad key".into());
        assert!(e.to_string().contains("bad key"));
    }

    #[test]
    fn from_io_error() {
        let io_err = std::io::Error::new(std::io::ErrorKind::NotFound, "gone");
        let mesh_err: MeshError = io_err.into();
        assert!(matches!(mesh_err, MeshError::Io(_)));
    }

    #[test]
    fn from_serde_error() {
        let serde_err = serde_json::from_str::<String>("not json").unwrap_err();
        let mesh_err: MeshError = serde_err.into();
        assert!(matches!(mesh_err, MeshError::Serialization(_)));
    }
}
