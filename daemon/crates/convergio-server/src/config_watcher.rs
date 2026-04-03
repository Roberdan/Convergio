//! Filesystem watcher for config hot-reload with debounce and diff.

use convergio_types::config::ConvergioConfig;
use notify::{Config, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use std::sync::{Arc, RwLock};
use std::time::Instant;

/// Fields that can be updated at runtime without a restart.
const HOT_RELOADABLE: &[&str] = &[
    "daemon.quiet_hours",
    "daemon.timezone",
    "daemon.auto_update",
    "inference.default_model",
    "inference.fallback",
    "kernel.max_tokens",
    "mesh.peers",
    "telegram.enabled",
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ConfigChange {
    pub field: String,
    pub reloadable: bool,
}

/// Compare two configs and return changed fields.
pub fn diff_configs(old: &ConvergioConfig, new: &ConvergioConfig) -> Vec<ConfigChange> {
    let mut changes = Vec::new();
    macro_rules! cmp {
        ($field:expr, $a:expr, $b:expr) => {
            if $a != $b {
                let name: &str = $field;
                changes.push(ConfigChange {
                    field: name.to_string(),
                    reloadable: HOT_RELOADABLE.contains(&name),
                });
            }
        };
    }
    cmp!("node.role", old.node.role, new.node.role);
    cmp!("node.name", old.node.name, new.node.name);
    cmp!("daemon.port", old.daemon.port, new.daemon.port);
    cmp!("daemon.quiet_hours", old.daemon.quiet_hours, new.daemon.quiet_hours);
    cmp!("daemon.timezone", old.daemon.timezone, new.daemon.timezone);
    cmp!("daemon.auto_update", old.daemon.auto_update, new.daemon.auto_update);
    cmp!("mesh.transport", old.mesh.transport, new.mesh.transport);
    cmp!("mesh.peers", old.mesh.peers, new.mesh.peers);
    cmp!("inference.default_model", old.inference.default_model, new.inference.default_model);
    cmp!("inference.fallback", old.inference.fallback, new.inference.fallback);
    cmp!("kernel.max_tokens", old.kernel.max_tokens, new.kernel.max_tokens);
    cmp!("telegram.enabled", old.telegram.enabled, new.telegram.enabled);
    changes
}

fn apply_reloadable(current: &mut ConvergioConfig, new: &ConvergioConfig) {
    current.daemon.quiet_hours = new.daemon.quiet_hours.clone();
    current.daemon.timezone = new.daemon.timezone.clone();
    current.daemon.auto_update = new.daemon.auto_update;
    current.inference.default_model = new.inference.default_model.clone();
    current.inference.fallback = new.inference.fallback.clone();
    current.kernel.max_tokens = new.kernel.max_tokens;
    current.mesh.peers = new.mesh.peers.clone();
    current.telegram.enabled = new.telegram.enabled;
}

const DEBOUNCE_MS: u128 = 500;

fn should_reload(last: &Instant) -> bool {
    last.elapsed().as_millis() >= DEBOUNCE_MS
}

/// Spawn a background thread that watches the config file for changes.
/// On modify, debounces 500 ms, re-parses, diffs, and applies
/// reloadable fields. Parse errors are logged, current config kept.
pub fn spawn_config_watcher(config: Arc<RwLock<ConvergioConfig>>) -> Result<(), String> {
    let path = super::config::config_path();
    let watch_dir = path
        .parent()
        .ok_or_else(|| "config path has no parent directory".to_string())?
        .to_path_buf();
    if !watch_dir.exists() {
        return Err(format!("config dir does not exist: {}", watch_dir.display()));
    }
    let file_name = path.file_name().map(|f| f.to_os_string()).unwrap_or_default();

    let cfg = Arc::clone(&config);
    let last_reload = Arc::new(std::sync::Mutex::new(Instant::now()));
    let lr = Arc::clone(&last_reload);
    let fname = file_name.clone();
    let cfg_path = path.clone();

    let mut watcher = RecommendedWatcher::new(
        move |res: Result<notify::Event, notify::Error>| {
            let event = match res {
                Ok(e) => e,
                Err(e) => {
                    tracing::warn!("[config] watcher error: {e}");
                    return;
                }
            };
            if !matches!(event.kind, EventKind::Modify(_)) {
                return;
            }
            let is_target = event
                .paths
                .iter()
                .any(|p| p.file_name().map(|f| f == fname).unwrap_or(false));
            if !is_target {
                return;
            }
            let mut last = lr.lock().unwrap_or_else(|e| e.into_inner());
            if !should_reload(&last) {
                return;
            }
            *last = Instant::now();
            drop(last);
            reload_config(&cfg, &cfg_path);
        },
        Config::default(),
    )
    .map_err(|e| format!("watcher init failed: {e}"))?;

    watcher
        .watch(&watch_dir, RecursiveMode::NonRecursive)
        .map_err(|e| format!("watch failed: {e}"))?;

    // Leak the watcher so it lives for the process lifetime.
    std::mem::forget(watcher);
    tracing::info!("[config] Watching {} for changes", path.display());
    Ok(())
}

fn reload_config(config: &Arc<RwLock<ConvergioConfig>>, path: &std::path::Path) {
    let contents = match std::fs::read_to_string(path) {
        Ok(c) => c,
        Err(e) => {
            tracing::warn!("[config] Failed to read {}: {e}", path.display());
            return;
        }
    };
    let new_cfg = match toml::from_str::<ConvergioConfig>(&contents) {
        Ok(c) => c,
        Err(e) => {
            tracing::warn!("[config] Parse error in {}: {e}", path.display());
            return;
        }
    };
    let mut guard = match config.write() {
        Ok(g) => g,
        Err(e) => {
            tracing::warn!("[config] RwLock poisoned: {e}");
            return;
        }
    };
    let changes = diff_configs(&guard, &new_cfg);
    if changes.is_empty() {
        return;
    }
    for change in &changes {
        if change.reloadable {
            tracing::info!("[config] Reloaded: {} changed", change.field);
        } else {
            tracing::warn!("[config] {} changed — requires restart", change.field);
        }
    }
    apply_reloadable(&mut guard, &new_cfg);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn diff_detects_port_change() {
        let old = ConvergioConfig::default();
        let mut new = ConvergioConfig::default();
        new.daemon.port = 9999;
        let changes = diff_configs(&old, &new);
        assert_eq!(changes.len(), 1);
        assert_eq!(changes[0].field, "daemon.port");
        assert!(!changes[0].reloadable);
    }

    #[test]
    fn diff_detects_reloadable_change() {
        let old = ConvergioConfig::default();
        let mut new = ConvergioConfig::default();
        new.kernel.max_tokens = 4096;
        let changes = diff_configs(&old, &new);
        assert_eq!(changes.len(), 1);
        assert!(changes[0].reloadable);
    }

    #[test]
    fn diff_no_changes() {
        let cfg = ConvergioConfig::default();
        assert!(diff_configs(&cfg, &cfg).is_empty());
    }

    #[test]
    fn apply_only_touches_reloadable() {
        let mut current = ConvergioConfig::default();
        let mut new = ConvergioConfig::default();
        new.daemon.port = 9999; // NOT reloadable
        new.kernel.max_tokens = 4096; // reloadable
        apply_reloadable(&mut current, &new);
        assert_eq!(current.daemon.port, 8420); // unchanged
        assert_eq!(current.kernel.max_tokens, 4096); // applied
    }
}
