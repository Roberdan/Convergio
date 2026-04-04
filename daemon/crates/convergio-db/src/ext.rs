//! DbExtension — provides the `db-pool` capability to the depgraph.
//!
//! The database pool is infrastructure, not a service with routes.
//! This extension exists solely to declare the `db-pool` capability
//! so that modules depending on it pass depgraph validation.

use convergio_types::extension::{Extension, Health};
use convergio_types::manifest::{Capability, Manifest, ModuleKind};

/// Minimal extension that declares the `db-pool` capability.
pub struct DbExtension;

impl Extension for DbExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-db".into(),
            description: "SQLite connection pool and migration runner".into(),
            version: "1.0.0".into(),
            kind: ModuleKind::Core,
            provides: vec![Capability {
                name: "db-pool".into(),
                version: "1.0.0".into(),
                description: "r2d2 SQLite connection pool".into(),
            }],
            requires: vec![],
            agent_tools: vec![],
        }
    }

    fn health(&self) -> Health {
        Health::Ok
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_provides_db_pool() {
        let ext = DbExtension;
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-db");
        assert!(m.provides.iter().any(|c| c.name == "db-pool"));
    }
}
