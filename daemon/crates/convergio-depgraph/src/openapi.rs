//! OpenAPI spec generation from Extension manifests and route metadata.
//!
//! Generates a minimal OpenAPI 3.0 document describing the system's
//! capabilities, modules, and tools. Full route introspection requires
//! extensions to declare route metadata (future enhancement).

use convergio_types::manifest::Manifest;
use serde_json::{json, Value};

/// Generate an OpenAPI 3.0 spec from a set of manifests.
///
/// Each module's capabilities become tagged paths, and agent tools
/// become operation descriptions under `/api/tools/{tool_name}`.
pub fn generate(manifests: &[Manifest]) -> Value {
    let mut paths = serde_json::Map::new();
    let mut tags: Vec<Value> = Vec::new();

    for m in manifests {
        tags.push(json!({
            "name": m.id,
            "description": m.description,
        }));

        // Capability endpoints
        for cap in &m.provides {
            let path = format!("/api/capabilities/{}", cap.name);
            paths.insert(
                path,
                json!({
                    "get": {
                        "tags": [&m.id],
                        "summary": &cap.description,
                        "operationId": format!("get_{}", cap.name.replace('-', "_")),
                        "responses": {
                            "200": {
                                "description": "Capability info",
                                "content": {
                                    "application/json": {
                                        "schema": { "type": "object" }
                                    }
                                }
                            }
                        }
                    }
                }),
            );
        }

        // Agent tool endpoints
        for tool in &m.agent_tools {
            let path = format!("/api/tools/{}", tool.name);
            paths.insert(
                path,
                json!({
                    "post": {
                        "tags": [&m.id],
                        "summary": &tool.description,
                        "operationId": format!("invoke_{}", tool.name.replace('-', "_")),
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": &tool.parameters_schema
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Tool result",
                                "content": {
                                    "application/json": {
                                        "schema": { "type": "object" }
                                    }
                                }
                            }
                        }
                    }
                }),
            );
        }
    }

    json!({
        "openapi": "3.0.3",
        "info": {
            "title": "Convergio Daemon API",
            "version": "0.1.0",
            "description": "Auto-generated from Extension manifests"
        },
        "tags": tags,
        "paths": paths
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use convergio_types::manifest::{Capability, ModuleKind, ToolSpec};

    #[test]
    fn generates_valid_openapi_structure() {
        let manifests = vec![Manifest {
            id: "test-module".into(),
            description: "A test module".into(),
            version: "1.0.0".into(),
            kind: ModuleKind::Extension,
            provides: vec![Capability {
                name: "test-cap".into(),
                version: "1.0.0".into(),
                description: "Test capability".into(),
            }],
            requires: vec![],
            agent_tools: vec![ToolSpec {
                name: "test-tool".into(),
                description: "A test tool".into(),
                parameters_schema: json!({"type": "object"}),
            }],
        }];

        let spec = generate(&manifests);
        assert_eq!(spec["openapi"], "3.0.3");
        assert!(spec["info"]["title"].is_string());
        assert!(spec["paths"]["/api/capabilities/test-cap"].is_object());
        assert!(spec["paths"]["/api/tools/test-tool"].is_object());
        assert_eq!(spec["tags"][0]["name"], "test-module");
    }

    #[test]
    fn empty_manifests_produces_empty_paths() {
        let spec = generate(&[]);
        assert!(spec["paths"].as_object().unwrap().is_empty());
        assert!(spec["tags"].as_array().unwrap().is_empty());
    }
}
