// Local path helpers — replaces convergio_core::platform_paths and config.
// CLI is a pure HTTP client; these are the only local filesystem paths it needs.

use std::path::PathBuf;

/// Root directory for Convergio local data: ~/.convergio
pub fn convergio_dir() -> PathBuf {
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".convergio")
}

/// Path to the main config file: ~/.convergio/config.toml
pub fn config_path() -> PathBuf {
    convergio_dir().join("config.toml")
}

/// Output directory for a project: ~/.convergio/projects/{name}/output
pub fn project_output_dir(name: &str) -> PathBuf {
    convergio_dir().join("projects").join(name).join("output")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn config_path_ends_with_config_toml() {
        let p = config_path();
        assert!(p.ends_with("config.toml"));
    }

    #[test]
    fn project_output_dir_contains_project_name() {
        let p = project_output_dir("acme");
        assert!(p.to_string_lossy().contains("acme"));
        assert!(p.ends_with("output"));
    }
}
