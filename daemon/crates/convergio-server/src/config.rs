//! Config loading from ~/.convergio/config.toml.
//!
//! Types live in convergio-types. This module handles I/O:
//! reading, parsing, writing defaults.

use convergio_types::config::ConvergioConfig;
use std::io;
use std::path::{Path, PathBuf};

/// Path to the config file. Overridable via `CONVERGIO_CONFIG` env var.
pub fn config_path() -> PathBuf {
    if let Ok(p) = std::env::var("CONVERGIO_CONFIG") {
        if !p.is_empty() {
            return PathBuf::from(p);
        }
    }
    dirs_path().join("config.toml")
}

fn dirs_path() -> PathBuf {
    std::env::var("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("."))
        .join(".convergio")
}

/// Load config from disk. Falls back to defaults when the file is missing
/// or empty. Logs a warning on parse errors and returns defaults.
pub fn load_config() -> ConvergioConfig {
    let path = config_path();
    match std::fs::read_to_string(&path) {
        Ok(contents) if !contents.trim().is_empty() => {
            match toml::from_str::<ConvergioConfig>(&contents) {
                Ok(cfg) => {
                    tracing::info!("[config] Loaded from {}", path.display());
                    cfg
                }
                Err(e) => {
                    tracing::warn!(
                        "[config] Parse error in {}: {e} — using defaults",
                        path.display()
                    );
                    ConvergioConfig::default()
                }
            }
        }
        Ok(_) => {
            tracing::info!("[config] {} is empty, using defaults", path.display());
            ConvergioConfig::default()
        }
        Err(_) => {
            tracing::info!("[config] No config.toml found, using defaults");
            ConvergioConfig::default()
        }
    }
}

/// Write a well-commented default config template to the given path.
pub fn write_default_config(path: &Path) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(path, super::config_defaults::DEFAULT_CONFIG_TEMPLATE)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn load_from_custom_path() {
        let dir = std::env::temp_dir().join("cvg-cfg-test");
        let _ = std::fs::create_dir_all(&dir);
        let path = dir.join("test.toml");
        let mut f = std::fs::File::create(&path).unwrap();
        writeln!(f, "[daemon]\nport = 9999").unwrap();
        std::env::set_var("CONVERGIO_CONFIG", path.to_str().unwrap());
        let cfg = load_config();
        assert_eq!(cfg.daemon.port, 9999);
        std::env::remove_var("CONVERGIO_CONFIG");
        let _ = std::fs::remove_dir_all(&dir);
    }

    #[test]
    fn missing_file_returns_defaults() {
        std::env::set_var("CONVERGIO_CONFIG", "/tmp/nonexistent.toml");
        let cfg = load_config();
        assert_eq!(cfg.daemon.port, 8420);
        std::env::remove_var("CONVERGIO_CONFIG");
    }
}
