//! Helper functions for spawn_monitor: file reading, path resolution.

use std::path::Path;

/// Read the last N lines from a file. Returns empty string if file is missing.
pub fn read_tail(path: &Path, lines: usize) -> String {
    std::fs::read_to_string(path)
        .unwrap_or_default()
        .lines()
        .rev()
        .take(lines)
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect::<Vec<_>>()
        .join("\n")
}

/// Resolve gh CLI path (launchd has minimal PATH).
pub fn resolve_gh_path() -> String {
    if let Ok(p) = std::env::var("CONVERGIO_GH_BIN") {
        return p;
    }
    let candidates = ["/opt/homebrew/bin/gh", "/usr/local/bin/gh"];
    for c in &candidates {
        if Path::new(c).exists() {
            return c.to_string();
        }
    }
    "gh".into()
}
