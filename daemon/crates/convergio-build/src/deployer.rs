//! Deploy logic — binary swap + launchd restart.

use crate::types::{BuildError, BuildResult};
use std::path::{Path, PathBuf};
use tracing::{info, warn};

/// Resolve the path to the running daemon binary.
pub fn running_binary_path() -> PathBuf {
    std::env::current_exe().unwrap_or_else(|_| PathBuf::from("/usr/local/bin/convergio"))
}

/// Resolve the newly-built release binary.
pub fn release_binary_path(workspace: &Path) -> PathBuf {
    workspace.join("target/release/convergio")
}

/// Deploy a new binary: backup old → copy new → verify → restart.
/// Returns the backup path of the old binary.
pub fn deploy(workspace: &Path) -> BuildResult<PathBuf> {
    let current = running_binary_path();
    let new_binary = release_binary_path(workspace);

    if !new_binary.exists() {
        return Err(BuildError::DeployFailed(
            "release binary not found — run build first".into(),
        ));
    }

    // 1. Backup current binary
    let backup = current.with_extension("bak");
    if current.exists() {
        std::fs::copy(&current, &backup)?;
        info!(backup = %backup.display(), "backed up current binary");
    }

    // 2. Copy new binary over current
    std::fs::copy(&new_binary, &current)?;
    info!(
        from = %new_binary.display(),
        to = %current.display(),
        "deployed new binary"
    );

    // 3. Ensure executable permission
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = std::fs::metadata(&current)?.permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&current, perms)?;
    }

    // 4. Restart via launchd
    match restart_launchd() {
        Ok(()) => info!("launchd service restarted"),
        Err(e) => warn!("launchd restart failed (manual restart needed): {e}"),
    }

    Ok(backup)
}

/// Restart the convergio launchd service.
fn restart_launchd() -> BuildResult<()> {
    let label = "com.convergio.daemon";

    // Stop
    let stop = std::process::Command::new("launchctl")
        .args(["stop", label])
        .output()?;
    if !stop.status.success() {
        warn!("launchctl stop failed (service may not be running)");
    }

    // Start (launchd will pick up the new binary)
    let start = std::process::Command::new("launchctl")
        .args(["start", label])
        .output()?;
    if !start.status.success() {
        let stderr = String::from_utf8_lossy(&start.stderr);
        return Err(BuildError::DeployFailed(format!(
            "launchctl start: {stderr}"
        )));
    }

    Ok(())
}

/// Rollback to the backup binary.
pub fn rollback(_workspace: &Path) -> BuildResult<()> {
    let current = running_binary_path();
    let backup = current.with_extension("bak");

    if !backup.exists() {
        return Err(BuildError::DeployFailed("no backup binary found".into()));
    }

    std::fs::copy(&backup, &current)?;
    info!("rolled back to backup binary");

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = std::fs::metadata(&current)?.permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&current, perms)?;
    }

    restart_launchd()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn running_binary_returns_path() {
        let path = running_binary_path();
        // In test context this is the test binary, not convergio
        assert!(!path.as_os_str().is_empty());
    }

    #[test]
    fn release_binary_path_correct() {
        let ws = PathBuf::from("/tmp/daemon");
        let p = release_binary_path(&ws);
        assert_eq!(p, PathBuf::from("/tmp/daemon/target/release/convergio"));
    }

    #[test]
    fn deploy_fails_without_binary() {
        let ws = PathBuf::from("/tmp/nonexistent-workspace");
        let result = deploy(&ws);
        assert!(result.is_err());
    }
}
