//! Capability registry: CRUD and query operations on node_capabilities.

use rusqlite::{params, Connection};
use std::collections::HashMap;

use crate::capability_types::{CapabilityMatch, CapabilityQuery, NodeCapabilities, NodeCapability};

/// Upsert capabilities for a peer into the node_capabilities table.
pub fn register_capabilities(
    conn: &Connection,
    peer_name: &str,
    caps: &[NodeCapability],
) -> Result<(), rusqlite::Error> {
    for cap in caps {
        let tags_json = serde_json::to_string(&cap.tags).unwrap_or_else(|_| "[]".into());
        let meta_json = serde_json::to_string(&cap.metadata).unwrap_or_else(|_| "{}".into());
        conn.execute(
            "INSERT INTO node_capabilities \
             (peer_name, capability_name, capability_version, tags_json, metadata_json) \
             VALUES (?1, ?2, ?3, ?4, ?5) \
             ON CONFLICT(peer_name, capability_name) DO UPDATE SET \
             capability_version = excluded.capability_version, \
             tags_json = excluded.tags_json, \
             metadata_json = excluded.metadata_json, \
             updated_at = datetime('now')",
            params![peer_name, cap.name, cap.version, tags_json, meta_json],
        )?;
    }
    Ok(())
}

/// Find peers whose capabilities match the required tags, sorted by score.
pub fn query_capable_peers(
    conn: &Connection,
    query: &CapabilityQuery,
) -> Result<Vec<CapabilityMatch>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT peer_name, capability_name, tags_json, capability_version \
         FROM node_capabilities",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
        ))
    })?;

    let required: Vec<String> = query.required_tags.iter().map(|t| t.to_string()).collect();
    let total_required = required.len() as f64;
    if total_required == 0.0 {
        return Ok(vec![]);
    }

    let mut peer_matches: HashMap<String, (f64, Vec<String>)> = HashMap::new();
    for row in rows {
        let (peer, cap_name, tags_str, version) = row?;
        if let Some(ref min_ver) = query.min_version {
            if &version < min_ver {
                continue;
            }
        }
        let tags: Vec<String> = serde_json::from_str(&tags_str).unwrap_or_default();
        let matched_tags: Vec<&String> = required.iter().filter(|rt| tags.contains(rt)).collect();
        if !matched_tags.is_empty() {
            let entry = peer_matches.entry(peer).or_insert((0.0, vec![]));
            entry.0 += matched_tags.len() as f64;
            entry.1.push(cap_name);
        }
    }

    let mut results: Vec<CapabilityMatch> = peer_matches
        .into_iter()
        .map(|(peer, (score, caps))| CapabilityMatch {
            peer_name: peer,
            score: score / total_required,
            matched_capabilities: caps,
        })
        .collect();
    results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    Ok(results)
}

/// Get all capabilities for a specific peer.
pub fn get_peer_capabilities(
    conn: &Connection,
    peer_name: &str,
) -> Result<Vec<NodeCapability>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT capability_name, capability_version, tags_json, metadata_json \
         FROM node_capabilities WHERE peer_name = ?1",
    )?;
    let rows = stmt.query_map(params![peer_name], |row| {
        let tags: Vec<String> = serde_json::from_str(&row.get::<_, String>(2)?).unwrap_or_default();
        let metadata: serde_json::Value =
            serde_json::from_str(&row.get::<_, String>(3)?).unwrap_or_default();
        Ok(NodeCapability {
            name: row.get(0)?,
            version: row.get(1)?,
            tags,
            metadata,
        })
    })?;
    rows.collect()
}

/// Remove all capabilities for a peer.
pub fn remove_peer_capabilities(conn: &Connection, peer_name: &str) -> Result<(), rusqlite::Error> {
    conn.execute(
        "DELETE FROM node_capabilities WHERE peer_name = ?1",
        params![peer_name],
    )?;
    Ok(())
}

/// List all capabilities grouped by peer.
pub fn list_all_capabilities(conn: &Connection) -> Result<Vec<NodeCapabilities>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT peer_name, capability_name, capability_version, \
         tags_json, metadata_json, updated_at \
         FROM node_capabilities ORDER BY peer_name, capability_name",
    )?;
    let rows = stmt.query_map([], |row| {
        let tags: Vec<String> = serde_json::from_str(&row.get::<_, String>(3)?).unwrap_or_default();
        let metadata: serde_json::Value =
            serde_json::from_str(&row.get::<_, String>(4)?).unwrap_or_default();
        Ok((
            row.get::<_, String>(0)?,
            NodeCapability {
                name: row.get(1)?,
                version: row.get(2)?,
                tags,
                metadata,
            },
            row.get::<_, String>(5)?,
        ))
    })?;

    let mut map: HashMap<String, (Vec<NodeCapability>, String)> = HashMap::new();
    for row in rows {
        let (peer, cap, updated) = row?;
        let entry = map.entry(peer).or_insert((vec![], updated.clone()));
        entry.0.push(cap);
        if updated > entry.1 {
            entry.1 = updated;
        }
    }

    Ok(map
        .into_iter()
        .map(|(peer, (caps, updated))| NodeCapabilities {
            peer_name: peer,
            capabilities: caps,
            last_updated: updated,
        })
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::capability_types::CapabilityTag;

    fn setup_db() -> Connection {
        let conn = Connection::open_in_memory().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "mesh", &crate::schema::migrations())
            .unwrap();
        conn
    }

    fn sample_cap(name: &str, tags: Vec<&str>) -> NodeCapability {
        NodeCapability {
            name: name.into(),
            version: "1.0.0".into(),
            tags: tags.into_iter().map(String::from).collect(),
            metadata: serde_json::json!({}),
        }
    }

    #[test]
    fn register_and_get() {
        let conn = setup_db();
        let caps = vec![sample_cap("llm", vec!["gpu", "inference"])];
        register_capabilities(&conn, "darwin-m4", &caps).unwrap();
        let result = get_peer_capabilities(&conn, "darwin-m4").unwrap();
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].name, "llm");
    }

    #[test]
    fn upsert_overwrites() {
        let conn = setup_db();
        let v1 = vec![sample_cap("llm", vec!["gpu"])];
        register_capabilities(&conn, "darwin-m4", &v1).unwrap();
        let v2 = vec![NodeCapability {
            name: "llm".into(),
            version: "2.0.0".into(),
            tags: vec!["gpu".into(), "inference".into()],
            metadata: serde_json::json!({}),
        }];
        register_capabilities(&conn, "darwin-m4", &v2).unwrap();
        let result = get_peer_capabilities(&conn, "darwin-m4").unwrap();
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].version, "2.0.0");
    }

    #[test]
    fn query_matches() {
        let conn = setup_db();
        let caps_m4 = [sample_cap("llm", vec!["gpu", "inference"])];
        let caps_a100 = [sample_cap("training", vec!["gpu", "compute"])];
        register_capabilities(&conn, "darwin-m4", &caps_m4).unwrap();
        register_capabilities(&conn, "linux-a100", &caps_a100).unwrap();
        let query = CapabilityQuery {
            required_tags: vec![CapabilityTag::Gpu, CapabilityTag::Inference],
            min_version: None,
        };
        let matches = query_capable_peers(&conn, &query).unwrap();
        assert_eq!(matches.len(), 2);
        assert!(matches[0].score > matches[1].score);
    }

    #[test]
    fn remove_and_list() {
        let conn = setup_db();
        register_capabilities(&conn, "darwin-m4", &[sample_cap("llm", vec!["gpu"])]).unwrap();
        register_capabilities(&conn, "linux-a100", &[sample_cap("t", vec!["compute"])]).unwrap();
        assert_eq!(list_all_capabilities(&conn).unwrap().len(), 2);
        remove_peer_capabilities(&conn, "darwin-m4").unwrap();
        assert!(get_peer_capabilities(&conn, "darwin-m4")
            .unwrap()
            .is_empty());
        assert_eq!(list_all_capabilities(&conn).unwrap().len(), 1);
    }
}
