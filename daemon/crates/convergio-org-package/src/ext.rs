//! Extension trait implementation for convergio-org-package.
//!
//! Owns the org_packages, org_tokens, and org_delegations tables.

use convergio_types::extension::{Extension, Health, Migration};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

/// Org-as-package extension — install, sandbox, sign, delegate.
pub struct OrgPackageExtension;

impl Extension for OrgPackageExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-org-package".to_string(),
            description: "Org-as-package ecosystem with sandbox, signing, delegation".to_string(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "org-package-install".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Install org packages from local, GitHub, or registry".to_string(),
                },
                Capability {
                    name: "org-sandbox".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Runtime sandbox with DB/route/IPC prefix isolation".to_string(),
                },
                Capability {
                    name: "org-delegation".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Inter-org task delegation with trust verification".to_string(),
                },
                Capability {
                    name: "org-signing".to_string(),
                    version: "1.0.0".to_string(),
                    description: "Package signing and verification".to_string(),
                },
            ],
            requires: vec![
                Dependency {
                    capability: "db-pool".to_string(),
                    version_req: ">=1.0.0".to_string(),
                    required: true,
                },
                Dependency {
                    capability: "ipc-bus".to_string(),
                    version_req: ">=1.0.0".to_string(),
                    required: true,
                },
            ],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        vec![
            Migration {
                version: 1,
                description: "installed org packages registry",
                up: "\
                    CREATE TABLE IF NOT EXISTS org_packages (\
                        id INTEGER PRIMARY KEY AUTOINCREMENT,\
                        name TEXT NOT NULL,\
                        version TEXT NOT NULL,\
                        description TEXT,\
                        author TEXT,\
                        source TEXT NOT NULL,\
                        manifest_json TEXT NOT NULL,\
                        signature TEXT,\
                        content_digest TEXT,\
                        db_prefix TEXT NOT NULL,\
                        route_prefix TEXT NOT NULL,\
                        ipc_prefix TEXT NOT NULL,\
                        installed_at TEXT DEFAULT (datetime('now')),\
                        UNIQUE(name, version)\
                    );\
                ",
            },
            Migration {
                version: 2,
                description: "scoped org tokens",
                up: "\
                    CREATE TABLE IF NOT EXISTS org_tokens (\
                        id INTEGER PRIMARY KEY AUTOINCREMENT,\
                        org_name TEXT NOT NULL,\
                        token_json TEXT NOT NULL,\
                        budget_api_calls INTEGER NOT NULL,\
                        budget_tokens_day INTEGER NOT NULL,\
                        budget_compute_secs INTEGER NOT NULL,\
                        issued_at TEXT DEFAULT (datetime('now')),\
                        expires_at TEXT NOT NULL,\
                        revoked INTEGER DEFAULT 0\
                    );\
                    CREATE INDEX IF NOT EXISTS idx_org_tokens_name \
                        ON org_tokens(org_name);\
                ",
            },
            Migration {
                version: 3,
                description: "inter-org delegation log",
                up: "\
                    CREATE TABLE IF NOT EXISTS org_delegations (\
                        id TEXT PRIMARY KEY,\
                        from_org TEXT NOT NULL,\
                        to_org TEXT NOT NULL,\
                        task TEXT NOT NULL,\
                        budget_tokens INTEGER,\
                        status TEXT DEFAULT 'pending',\
                        deadline TEXT,\
                        created_at TEXT DEFAULT (datetime('now')),\
                        completed_at TEXT\
                    );\
                    CREATE INDEX IF NOT EXISTS idx_org_deleg_from \
                        ON org_delegations(from_org);\
                    CREATE INDEX IF NOT EXISTS idx_org_deleg_to \
                        ON org_delegations(to_org);\
                ",
            },
        ]
    }

    fn health(&self) -> Health {
        Health::Ok
    }
}
