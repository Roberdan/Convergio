//! DepgraphExtension — impl Extension for the depgraph module.

use convergio_types::extension::{AppContext, ExtResult, Extension, Health, Metric};
use convergio_types::manifest::{Capability, Dependency, Manifest, ModuleKind};

use crate::graph::DepGraph;
use crate::routes::{self, DepgraphState};

/// Extension that validates the dependency graph and serves graph/OpenAPI routes.
pub struct DepgraphExtension {
    manifests: Vec<Manifest>,
}

impl Default for DepgraphExtension {
    fn default() -> Self {
        Self::new(vec![])
    }
}

impl DepgraphExtension {
    pub fn new(manifests: Vec<Manifest>) -> Self {
        Self { manifests }
    }

    /// Run startup validation — call this before serving traffic.
    /// Returns Ok(()) if graph is valid, Err with details otherwise.
    pub fn validate_at_startup(&self) -> Result<(), String> {
        match DepGraph::validate(&self.manifests) {
            Ok(()) => {
                tracing::info!(
                    modules = self.manifests.len(),
                    "dependency graph validated successfully"
                );
                Ok(())
            }
            Err(errors) => {
                for e in &errors {
                    tracing::error!(?e, "dependency graph validation error");
                }
                Err(format!("dependency graph has {} error(s)", errors.len()))
            }
        }
    }
}

impl Extension for DepgraphExtension {
    fn manifest(&self) -> Manifest {
        Manifest {
            id: "convergio-depgraph".into(),
            description: "Dependency graph validation, OpenAPI generation, \
                          capability listing"
                .into(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            kind: ModuleKind::Platform,
            provides: vec![
                Capability {
                    name: "dep-graph".into(),
                    version: env!("CARGO_PKG_VERSION").to_string(),
                    description: "Dependency graph validation and \
                                  visualization"
                        .into(),
                },
                Capability {
                    name: "openapi-gen".into(),
                    version: env!("CARGO_PKG_VERSION").to_string(),
                    description: "Auto-generated OpenAPI spec from \
                                  Extension manifests"
                        .into(),
                },
                Capability {
                    name: "capability-list".into(),
                    version: env!("CARGO_PKG_VERSION").to_string(),
                    description: "Full system capability listing".into(),
                },
            ],
            requires: vec![Dependency {
                capability: "types-core".into(),
                version_req: ">=0.1.0".into(),
                required: false,
            }],
            agent_tools: vec![],
        }
    }

    fn routes(&self, _ctx: &AppContext) -> Option<axum::Router> {
        let state = DepgraphState::new(self.manifests.clone());
        Some(routes::router(state))
    }

    fn on_start(&self, _ctx: &AppContext) -> ExtResult<()> {
        self.validate_at_startup()
            .map_err(|e| Box::new(std::io::Error::other(e)) as Box<_>)?;
        Ok(())
    }

    fn health(&self) -> Health {
        match DepGraph::validate(&self.manifests) {
            Ok(()) => Health::Ok,
            Err(errors) => Health::Degraded {
                reason: format!("{} validation error(s)", errors.len()),
            },
        }
    }

    fn metrics(&self) -> Vec<Metric> {
        let graph = DepGraph::from_manifests(&self.manifests);
        vec![
            Metric {
                name: "depgraph_modules".into(),
                value: graph.nodes.len() as f64,
                labels: vec![],
            },
            Metric {
                name: "depgraph_edges".into(),
                value: graph.edges.len() as f64,
                labels: vec![],
            },
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_has_correct_id() {
        let ext = DepgraphExtension::default();
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-depgraph");
    }

    #[test]
    fn provides_three_capabilities() {
        let ext = DepgraphExtension::default();
        let m = ext.manifest();
        assert_eq!(m.provides.len(), 3);
    }

    #[test]
    fn health_ok_with_empty_graph() {
        let ext = DepgraphExtension::default();
        assert!(matches!(ext.health(), Health::Ok));
    }

    #[test]
    fn metrics_report_counts() {
        let ext = DepgraphExtension::default();
        let metrics = ext.metrics();
        assert_eq!(metrics.len(), 2);
        assert_eq!(metrics[0].name, "depgraph_modules");
    }

    #[test]
    fn startup_validation_passes_empty() {
        let ext = DepgraphExtension::default();
        assert!(ext.validate_at_startup().is_ok());
    }

    #[test]
    fn routes_are_provided() {
        let ext = DepgraphExtension::default();
        let ctx = AppContext::new();
        assert!(ext.routes(&ctx).is_some());
    }
}
