//! INI parser and serialiser for ~/.claude/config/peers.conf.
//!
//! Format: `[section_name]` + `key=value` lines.
//! `[mesh]` for global config, `[peer_name]` for each peer.

use std::collections::BTreeMap;

use crate::peers_types::{PeerConfig, PeersError};

fn require(map: &BTreeMap<String, String>, key: &str, peer: &str) -> Result<String, PeersError> {
    map.get(key)
        .cloned()
        .ok_or_else(|| PeersError::MissingField {
            peer: peer.to_owned(),
            field: key.to_owned(),
        })
}

fn parse_capabilities(raw: &str) -> Vec<String> {
    raw.split(',')
        .map(|s| s.trim().to_owned())
        .filter(|s| !s.is_empty())
        .collect()
}

fn build_peer(name: &str, kv: &BTreeMap<String, String>) -> Result<PeerConfig, PeersError> {
    Ok(PeerConfig {
        ssh_alias: require(kv, "ssh_alias", name)?,
        user: require(kv, "user", name)?,
        os: require(kv, "os", name)?,
        tailscale_ip: require(kv, "tailscale_ip", name)?,
        dns_name: require(kv, "dns_name", name)?,
        capabilities: parse_capabilities(&require(kv, "capabilities", name)?),
        role: require(kv, "role", name)?,
        status: kv
            .get("status")
            .cloned()
            .unwrap_or_else(|| "active".to_owned()),
        thunderbolt_ip: kv.get("thunderbolt_ip").cloned(),
        lan_ip: kv.get("lan_ip").cloned(),
        mac_address: kv.get("mac_address").cloned(),
        gh_account: kv.get("gh_account").cloned(),
        runners: kv.get("runners").and_then(|v| v.parse::<u32>().ok()),
        runner_paths: kv.get("runner_paths").cloned(),
        aliases: kv
            .get("aliases")
            .map(|v| parse_capabilities(v))
            .unwrap_or_default(),
    })
}

fn flush_section(
    section: &Option<String>,
    kv: &BTreeMap<String, String>,
    secret: &mut String,
    peers: &mut BTreeMap<String, PeerConfig>,
) -> Result<(), PeersError> {
    if let Some(name) = section {
        if name == "mesh" {
            if let Some(s) = kv.get("shared_secret") {
                *secret = s.clone();
            }
        } else {
            let cfg = build_peer(name, kv)?;
            peers.insert(name.clone(), cfg);
        }
    }
    Ok(())
}

pub fn parse_ini(text: &str) -> Result<(String, BTreeMap<String, PeerConfig>), PeersError> {
    let mut shared_secret = String::new();
    let mut peers: BTreeMap<String, PeerConfig> = BTreeMap::new();
    let mut current_section: Option<String> = None;
    let mut current_kv: BTreeMap<String, String> = BTreeMap::new();

    for (lineno, raw) in text.lines().enumerate() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if line.starts_with('[') && line.ends_with(']') {
            flush_section(
                &current_section,
                &current_kv,
                &mut shared_secret,
                &mut peers,
            )?;
            current_section = Some(line[1..line.len() - 1].to_owned());
            current_kv = BTreeMap::new();
        } else if let Some(eq) = line.find('=') {
            let key = line[..eq].trim().to_owned();
            let val = line[eq + 1..].trim().to_owned();
            current_kv.insert(key, val);
        } else {
            return Err(PeersError::Parse {
                line: lineno + 1,
                msg: format!("unexpected content: {line}"),
            });
        }
    }
    flush_section(
        &current_section,
        &current_kv,
        &mut shared_secret,
        &mut peers,
    )?;
    Ok((shared_secret, peers))
}

fn caps_str(caps: &[String]) -> String {
    caps.join(",")
}

pub fn peer_to_ini(name: &str, p: &PeerConfig) -> String {
    let mut out = format!(
        "[{name}]\nssh_alias={}\nuser={}\nos={}\n\
         tailscale_ip={}\ndns_name={}\ncapabilities={}\n\
         role={}\nstatus={}\n",
        p.ssh_alias,
        p.user,
        p.os,
        p.tailscale_ip,
        p.dns_name,
        caps_str(&p.capabilities),
        p.role,
        p.status,
    );
    if let Some(ref tb) = p.thunderbolt_ip {
        out.push_str(&format!("thunderbolt_ip={tb}\n"));
    }
    if let Some(ref lan) = p.lan_ip {
        out.push_str(&format!("lan_ip={lan}\n"));
    }
    if let Some(ref mac) = p.mac_address {
        out.push_str(&format!("mac_address={mac}\n"));
    }
    if let Some(ref gh) = p.gh_account {
        out.push_str(&format!("gh_account={gh}\n"));
    }
    if let Some(r) = p.runners {
        out.push_str(&format!("runners={r}\n"));
    }
    if let Some(ref rp) = p.runner_paths {
        out.push_str(&format!("runner_paths={rp}\n"));
    }
    if !p.aliases.is_empty() {
        out.push_str(&format!("aliases={}\n", p.aliases.join(",")));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_basic_ini() {
        let ini = "[mesh]\nshared_secret=s3cr3t\n\n\
                   [node1]\nssh_alias=n1\nuser=bob\nos=linux\n\
                   tailscale_ip=100.1.2.3\ndns_name=n1.ts.net\n\
                   capabilities=claude\nrole=worker\nstatus=active\n";
        let (secret, peers) = parse_ini(ini).unwrap();
        assert_eq!(secret, "s3cr3t");
        assert_eq!(peers.len(), 1);
        assert_eq!(peers["node1"].user, "bob");
    }

    #[test]
    fn roundtrip_peer_to_ini() {
        let peer = PeerConfig {
            ssh_alias: "a".into(),
            user: "u".into(),
            os: "macos".into(),
            tailscale_ip: "100.0.0.1".into(),
            dns_name: "d.ts.net".into(),
            capabilities: vec!["claude".into(), "copilot".into()],
            role: "worker".into(),
            status: "active".into(),
            thunderbolt_ip: None,
            lan_ip: None,
            mac_address: None,
            gh_account: None,
            runners: None,
            runner_paths: None,
            aliases: vec![],
        };
        let ini = peer_to_ini("test", &peer);
        assert!(ini.contains("[test]"));
        assert!(ini.contains("capabilities=claude,copilot"));
    }
}
