//! Platform-aware directory resolution.
//!
//! macOS: ~/Library/Application Support/Convergio
//! Linux: ~/.local/share/convergio
//! Windows: %APPDATA%/Convergio
//! Fallback: ~/.convergio/

use std::path::PathBuf;

/// Primary Convergio data directory.
pub fn convergio_data_dir() -> PathBuf {
    if let Some(data) = dirs::data_dir() {
        return data.join("Convergio");
    }
    dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".convergio")
}

/// Output directory for a named project.
pub fn project_output_dir(project_name: &str) -> PathBuf {
    convergio_data_dir()
        .join("projects")
        .join(project_name)
        .join("output")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn data_dir_is_absolute_or_fallback() {
        let dir = convergio_data_dir();
        let name = dir.file_name().unwrap().to_str().unwrap();
        assert!(
            name == "Convergio" || name == ".convergio",
            "unexpected dir name: {name}"
        );
    }

    #[test]
    fn project_output_dir_structure() {
        let out = project_output_dir("my-app");
        assert!(out.ends_with("projects/my-app/output"));
    }
}
