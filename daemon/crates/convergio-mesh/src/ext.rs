//! MeshExtension: Extension trait implementation.

use convergio_db::pool::ConnPool;
use convergio_telemetry::health::{ComponentHealth, HealthCheck};
use convergio_telemetry::metrics::MetricSource;
use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric, Migration};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

use crate::types::MeshStats;

pub struct MeshExtension {
    pool: ConnPool,
}

impl MeshExtension {
    pub fn new(pool: ConnPool) -> Self {
        Self { pool }
    }

    pub fn pool(&self) -> &ConnPool {
        &self.pool
    }

    pub fn stats(&self) -> Result<MeshStats, String> {
        let conn = self.pool.get().map_err(|e| e.to_string())?;
        let peers_online: u64 = conn
            .query_row(
                "SELECT count(*) FROM peer_heartbeats \
                 WHERE last_seen > unixepoch() - 600",
                [],
                |r| r.get(0),
            )
            .unwrap_or(0);
        let total_synced: u64 = conn
            .query_row(
                "SELECT COALESCE(SUM(total_applied), 0) FROM mesh_sync_stats",
                [],
                |r| r.get(0),
            )
            .unwrap_or(0);
        let last_sync_latency_ms: Option<i64> = conn
            .query_row(
                "SELECT last_latency_ms FROM mesh_sync_stats \
                 ORDER BY last_sync_at DESC LIMIT 1",
                [],
                |r| r.get(0),
            )
            .ok();
        Ok(MeshStats {
            peers_online,
            total_synced,
            last_sync_latency_ms,
        })
    }
}

impl Extension for MeshExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-mesh".into(),
            description: "Peer discovery, delta sync, delegation tracking".into(),
            version: "0.1.0".into(),
            kind: ModuleKind::Core,
            provides: vec![
                Capability {
                    name: "peer-sync".into(),
                    version: "0.1.0".into(),
                    description: "Timestamp-based LWW replication".into(),
                },
                Capability {
                    name: "peer-discovery".into(),
                    version: "0.1.0".into(),
                    description: "Peer registry and health probing".into(),
                },
                Capability {
                    name: "delegation-tracking".into(),
                    version: "0.1.0".into(),
                    description: "Remote task delegation progress".into(),
                },
            ],
            requires: vec![Dependency {
                capability: "db-pool".into(),
                version_req: ">=0.1.0".into(),
                required: true,
            }],
            agent_tools: vec![],
        }
    }

    fn migrations(&self) -> Vec<Migration> {
        crate::schema::migrations()
    }

    fn health(&self) -> Health {
        match self.stats() {
            Ok(s) if s.peers_online > 0 => Health::Ok,
            Ok(_) => Health::Degraded {
                reason: "no peers online".into(),
            },
            Err(e) => Health::Down {
                reason: format!("mesh stats failed: {e}"),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        match self.stats() {
            Ok(s) => {
                let mut m = vec![
                    Metric {
                        name: "mesh_peers_online".into(),
                        value: s.peers_online as f64,
                        labels: vec![],
                    },
                    Metric {
                        name: "mesh_total_synced".into(),
                        value: s.total_synced as f64,
                        labels: vec![],
                    },
                ];
                if let Some(lat) = s.last_sync_latency_ms {
                    m.push(Metric {
                        name: "mesh_sync_latency_ms".into(),
                        value: lat as f64,
                        labels: vec![],
                    });
                }
                m
            }
            Err(_) => vec![],
        }
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        tracing::info!("Mesh extension started");
        Ok(())
    }

    fn on_shutdown(&self) -> ExtResult<()> {
        tracing::info!("Mesh extension shutdown");
        Ok(())
    }
}

impl HealthCheck for MeshExtension {
    fn name(&self) -> &str {
        "mesh"
    }

    fn check(&self) -> ComponentHealth {
        let (status, message) = match self.stats() {
            Ok(s) => (
                if s.peers_online > 0 {
                    Health::Ok
                } else {
                    Health::Degraded {
                        reason: "no peers".into(),
                    }
                },
                Some(format!(
                    "{} peers, {} synced",
                    s.peers_online, s.total_synced
                )),
            ),
            Err(e) => (Health::Down { reason: e }, None),
        };
        ComponentHealth {
            name: "mesh".into(),
            status,
            message,
        }
    }
}

impl MetricSource for MeshExtension {
    fn name(&self) -> &str {
        "mesh"
    }

    fn collect(&self) -> Vec<Metric> {
        self.metrics()
    }
}
