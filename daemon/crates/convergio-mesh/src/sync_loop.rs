//! Background mesh sync loop.
//!
//! Spawns a tokio task that periodically syncs all SYNC_TABLES
//! with every active peer in the peers registry.

use std::collections::HashMap;
use std::time::{Duration, Instant};

use convergio_db::pool::ConnPool;
use tracing::{error, info, warn};

use crate::peers_registry::peers_conf_path_from_env;
use crate::peers_types::{PeerConfig, PeersRegistry};
use crate::sync::sync_table_with_peer;
use crate::transport::{resolve_best_addr, update_mesh_sync_stats};
use crate::types::SYNC_TABLES;

/// Spawn background tokio task: every `interval`, sync all tables with all active peers.
pub fn spawn_sync_loop(pool: ConnPool, interval: Duration) {
    tokio::spawn(async move {
        info!(interval_secs = interval.as_secs(), "mesh sync loop started");
        loop {
            tokio::time::sleep(interval).await;
            let pool_clone = pool.clone();
            if let Err(e) = tokio::task::spawn_blocking(move || run_sync_round(&pool_clone)).await {
                error!("sync round task panicked: {e}");
            }
        }
    });
}

fn run_sync_round(pool: &ConnPool) {
    let conf_path = std::path::PathBuf::from(peers_conf_path_from_env());
    let registry = match PeersRegistry::load(&conf_path) {
        Ok(r) => r,
        Err(e) => {
            warn!("peers registry load failed: {e}");
            return;
        }
    };

    let conn = match pool.get() {
        Ok(c) => c,
        Err(e) => {
            error!("db pool get failed: {e}");
            return;
        }
    };

    for (name, peer) in registry.list_active() {
        let fields = peer_to_fields(peer);
        let Some(addr) = resolve_best_addr(name, &fields) else {
            warn!(peer = name, "no reachable address, skipping");
            continue;
        };

        let started = Instant::now();
        let mut total_sent = 0usize;
        let mut total_received = 0usize;
        let mut total_applied = 0usize;

        for table in SYNC_TABLES {
            let (sent, received, applied) = sync_table_with_peer(&conn, &addr, table);
            total_sent += sent;
            total_received += received;
            total_applied += applied;
            if sent > 0 || received > 0 || applied > 0 {
                info!(peer = name, table, sent, received, applied, "table synced");
            }
        }

        let latency_ms = started.elapsed().as_millis() as i64;
        update_mesh_sync_stats(
            &conn,
            &addr,
            total_sent,
            total_received,
            total_applied,
            latency_ms,
        );

        info!(
            peer = name,
            addr = %addr,
            sent = total_sent,
            received = total_received,
            applied = total_applied,
            latency_ms,
            "sync round complete"
        );
    }
}

fn peer_to_fields(peer: &PeerConfig) -> HashMap<String, String> {
    let mut map = HashMap::new();
    if let Some(ip) = &peer.thunderbolt_ip {
        map.insert("thunderbolt_ip".into(), ip.clone());
    }
    if let Some(ip) = &peer.lan_ip {
        map.insert("lan_ip".into(), ip.clone());
    }
    if !peer.tailscale_ip.is_empty() {
        map.insert("tailscale_ip".into(), peer.tailscale_ip.clone());
    }
    map
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::peers_types::PeerConfig;

    fn make_peer(tailscale_ip: &str) -> PeerConfig {
        PeerConfig {
            ssh_alias: "test".into(),
            user: "user".into(),
            os: "linux".into(),
            tailscale_ip: tailscale_ip.into(),
            dns_name: "test.ts.net".into(),
            capabilities: vec![],
            role: "worker".into(),
            status: "active".into(),
            thunderbolt_ip: None,
            lan_ip: None,
            mac_address: None,
            gh_account: None,
            runners: None,
            runner_paths: None,
            aliases: vec![],
        }
    }

    #[test]
    fn peer_to_fields_includes_tailscale() {
        let peer = make_peer("100.0.0.1");
        let fields = peer_to_fields(&peer);
        assert_eq!(
            fields.get("tailscale_ip").map(String::as_str),
            Some("100.0.0.1")
        );
    }

    #[test]
    fn peer_to_fields_thunderbolt_absent() {
        let peer = make_peer("100.0.0.2");
        let fields = peer_to_fields(&peer);
        assert!(!fields.contains_key("thunderbolt_ip"));
    }

    #[test]
    fn peer_to_fields_with_all_transports() {
        let mut peer = make_peer("100.0.0.3");
        peer.thunderbolt_ip = Some("10.0.0.1".into());
        peer.lan_ip = Some("192.168.1.1".into());
        let fields = peer_to_fields(&peer);
        assert_eq!(fields.len(), 3);
    }
}
