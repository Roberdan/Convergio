//! Config validation — helpful messages that tell users what to fix.

use convergio_types::config::ConvergioConfig;

const KNOWN_ROLES: &[&str] = &["standalone", "coordinator", "worker"];
const KNOWN_TRANSPORTS: &[&str] = &["lan", "tailscale", "manual"];
const KNOWN_DISCOVERY: &[&str] = &["mdns", "static", "tailscale"];

/// Validate a loaded config and return human-readable warnings.
/// An empty Vec means everything looks good.
pub fn validate(config: &ConvergioConfig) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();

    if !KNOWN_ROLES.contains(&config.node.role.as_str()) {
        issues.push(format!(
            "[node] role '{}' is not recognized. Expected: {}",
            config.node.role,
            KNOWN_ROLES.join(", ")
        ));
    }
    if config.daemon.port < 1024 {
        issues.push(format!(
            "[daemon] port {} is below 1024. Use 1024-65535.",
            config.daemon.port
        ));
    }
    if let Some(ref tz) = config.daemon.timezone {
        if !looks_like_iana_tz(tz) {
            issues.push(format!(
                "[daemon] timezone '{tz}' doesn't look like IANA (expected Area/City)."
            ));
        }
    }
    if let Some(ref qh) = config.daemon.quiet_hours {
        if !looks_like_time_range(qh) {
            issues.push(format!(
                "[daemon] quiet_hours '{qh}' should be HH:MM-HH:MM."
            ));
        }
    }
    if !KNOWN_TRANSPORTS.contains(&config.mesh.transport.as_str()) {
        issues.push(format!(
            "[mesh] transport '{}' is not recognized. Expected: {}",
            config.mesh.transport,
            KNOWN_TRANSPORTS.join(", ")
        ));
    }
    if !KNOWN_DISCOVERY.contains(&config.mesh.discovery.as_str()) {
        issues.push(format!(
            "[mesh] discovery '{}' is not recognized. Expected: {}",
            config.mesh.discovery,
            KNOWN_DISCOVERY.join(", ")
        ));
    }
    if config.kernel.max_tokens == 0 {
        issues.push("[kernel] max_tokens must be > 0.".to_string());
    }
    issues
}

fn looks_like_iana_tz(s: &str) -> bool {
    s.contains('/') && !s.contains(' ') && s.len() >= 5
}

fn looks_like_time_range(s: &str) -> bool {
    let parts: Vec<&str> = s.split('-').collect();
    if parts.len() != 2 {
        return false;
    }
    parts.iter().all(|p| {
        let hm: Vec<&str> = p.split(':').collect();
        if hm.len() != 2 {
            return false;
        }
        let h = hm[0].parse::<u32>();
        let m = hm[1].parse::<u32>();
        matches!((h, m), (Ok(0..=23), Ok(0..=59)))
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use convergio_types::config::ConvergioConfig;

    #[test]
    fn valid_defaults_no_warnings() {
        assert!(validate(&ConvergioConfig::default()).is_empty());
    }

    #[test]
    fn bad_port_caught() {
        let mut cfg = ConvergioConfig::default();
        cfg.daemon.port = 80;
        assert!(validate(&cfg).iter().any(|i| i.contains("port")));
    }

    #[test]
    fn bad_role_caught() {
        let mut cfg = ConvergioConfig::default();
        cfg.node.role = "boss".to_string();
        assert!(validate(&cfg).iter().any(|i| i.contains("role")));
    }

    #[test]
    fn bad_timezone_caught() {
        let mut cfg = ConvergioConfig::default();
        cfg.daemon.timezone = Some("nope".to_string());
        assert!(validate(&cfg).iter().any(|i| i.contains("timezone")));
    }

    #[test]
    fn bad_quiet_hours_caught() {
        let mut cfg = ConvergioConfig::default();
        cfg.daemon.quiet_hours = Some("midnight".to_string());
        assert!(validate(&cfg).iter().any(|i| i.contains("quiet_hours")));
    }

    #[test]
    fn valid_quiet_hours_accepted() {
        let mut cfg = ConvergioConfig::default();
        cfg.daemon.quiet_hours = Some("23:00-07:00".to_string());
        assert!(!validate(&cfg).iter().any(|i| i.contains("quiet_hours")));
    }

    #[test]
    fn bad_transport_caught() {
        let mut cfg = ConvergioConfig::default();
        cfg.mesh.transport = "pigeon".to_string();
        assert!(validate(&cfg).iter().any(|i| i.contains("transport")));
    }

    #[test]
    fn zero_max_tokens_caught() {
        let mut cfg = ConvergioConfig::default();
        cfg.kernel.max_tokens = 0;
        assert!(validate(&cfg).iter().any(|i| i.contains("max_tokens")));
    }
}
