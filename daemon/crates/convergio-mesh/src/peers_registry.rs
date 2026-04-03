//! PeersRegistry: load, save, and mutation operations.

use std::path::Path;

use crate::peers_parser::{parse_ini, peer_to_ini};
use crate::peers_types::{PeerConfig, PeersError, PeersRegistry};

/// Path to peers.conf: CONVERGIO_PEERS_CONF env var or default.
pub fn peers_conf_path_from_env() -> String {
    std::env::var("CONVERGIO_PEERS_CONF").unwrap_or_else(|_| {
        let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
        format!("{home}/.claude/config/peers.conf")
    })
}

impl PeersRegistry {
    pub fn load(path: &Path) -> Result<Self, PeersError> {
        let text = std::fs::read_to_string(path)?;
        let (shared_secret, peers) = parse_ini(&text)?;
        Ok(Self { shared_secret, peers })
    }

    pub fn save(&self, path: &Path) -> Result<(), PeersError> {
        let mut out = String::new();
        out.push_str("[mesh]\n");
        out.push_str(&format!("shared_secret={}\n", self.shared_secret));
        for (name, cfg) in &self.peers {
            out.push('\n');
            out.push_str(&peer_to_ini(name, cfg));
        }
        std::fs::write(path, out)?;
        Ok(())
    }

    pub fn add_peer(&mut self, name: &str, config: PeerConfig) {
        self.peers.insert(name.to_owned(), config);
    }

    pub fn remove_peer(&mut self, name: &str) -> Option<PeerConfig> {
        self.peers.remove(name)
    }

    pub fn update_role(
        &mut self,
        name: &str,
        role: &str,
    ) -> Result<(), PeersError> {
        self.peers
            .get_mut(name)
            .ok_or_else(|| PeersError::NotFound(name.to_owned()))
            .map(|p| p.role = role.to_owned())
    }

    pub fn get_coordinator(&self) -> Option<(&str, &PeerConfig)> {
        self.peers
            .iter()
            .find(|(_, p)| p.role == "coordinator")
            .map(|(n, p)| (n.as_str(), p))
    }

    pub fn list_active(&self) -> Vec<(&str, &PeerConfig)> {
        self.peers
            .iter()
            .filter(|(_, p)| p.status == "active")
            .map(|(n, p)| (n.as_str(), p))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    const PEERS_INI: &str = "\
[mesh]
shared_secret=test-secret

[node1]
ssh_alias=n1
user=alice
os=macos
tailscale_ip=100.0.0.1
dns_name=n1.ts.net
capabilities=claude,copilot
role=coordinator
status=active

[node2]
ssh_alias=n2
user=bob
os=linux
tailscale_ip=100.0.0.2
dns_name=n2.ts.net
capabilities=claude
role=worker
status=active
";

    fn load_from_str(s: &str) -> PeersRegistry {
        let f = NamedTempFile::new().unwrap();
        std::fs::write(f.path(), s).unwrap();
        PeersRegistry::load(f.path()).unwrap()
    }

    #[test]
    fn load_and_query() {
        let reg = load_from_str(PEERS_INI);
        assert_eq!(reg.shared_secret, "test-secret");
        assert_eq!(reg.peers.len(), 2);
        assert_eq!(reg.list_active().len(), 2);
    }

    #[test]
    fn find_coordinator() {
        let reg = load_from_str(PEERS_INI);
        let (name, _) = reg.get_coordinator().unwrap();
        assert_eq!(name, "node1");
    }

    #[test]
    fn roundtrip_save_load() {
        let reg = load_from_str(PEERS_INI);
        let tmp = NamedTempFile::new().unwrap();
        reg.save(tmp.path()).unwrap();
        let reg2 = PeersRegistry::load(tmp.path()).unwrap();
        assert_eq!(reg2.peers.len(), reg.peers.len());
        assert_eq!(reg2.shared_secret, reg.shared_secret);
    }

    #[test]
    fn add_remove_peer() {
        let mut reg = load_from_str(PEERS_INI);
        let peer = PeerConfig {
            ssh_alias: "n3".into(), user: "eve".into(), os: "linux".into(),
            tailscale_ip: "100.0.0.3".into(), dns_name: "n3.ts.net".into(),
            capabilities: vec!["claude".into()],
            role: "worker".into(), status: "active".into(),
            thunderbolt_ip: None, lan_ip: None, mac_address: None,
            gh_account: None, runners: None, runner_paths: None,
            aliases: vec![],
        };
        reg.add_peer("node3", peer);
        assert_eq!(reg.peers.len(), 3);
        reg.remove_peer("node3");
        assert_eq!(reg.peers.len(), 2);
    }
}
