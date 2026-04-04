//! Real agent process spawner — creates worktree, writes instructions, launches process.
//!
//! This is the bridge between "daemon decides" and "daemon acts".
//! Supports multiple backends: Claude CLI, API call, script.

use std::path::{Path, PathBuf};
use std::process::Command;

use crate::types::{RuntimeError, RuntimeResult};

/// Which backend to use for the agent process.
#[derive(Debug, Clone)]
pub enum SpawnBackend {
    /// Claude Code CLI with tool access (for complex tasks needing file ops).
    ClaudeCli { model: String },
    /// Direct shell command (for deterministic/scripted tasks).
    Script { command: String, args: Vec<String> },
}

/// Result of spawning an agent process.
#[derive(Debug)]
pub struct SpawnedProcess {
    pub pid: u32,
    pub workspace: PathBuf,
    pub backend: String,
}

/// Create a git worktree for the agent. Returns the worktree path.
pub fn create_worktree(repo_root: &Path, name: &str) -> RuntimeResult<PathBuf> {
    let wt_path = repo_root.join(".worktrees").join(name);
    if wt_path.exists() {
        return Err(RuntimeError::Internal(format!(
            "worktree already exists: {}",
            wt_path.display()
        )));
    }
    // Create worktree WITH a branch (not detached) so agent can push + PR
    let branch = format!("agent/{name}");
    let output = Command::new("git")
        .args(["worktree", "add", "-b", &branch])
        .arg(&wt_path)
        .arg("HEAD")
        .current_dir(repo_root)
        .output()
        .map_err(|e| RuntimeError::Internal(format!("git worktree: {e}")))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(RuntimeError::Internal(format!(
            "git worktree failed: {stderr}"
        )));
    }
    Ok(wt_path)
}

/// Write task instructions to a file the agent will read.
pub fn write_instructions(workspace: &Path, instructions: &str) -> RuntimeResult<PathBuf> {
    let path = workspace.join("TASK.md");
    std::fs::write(&path, instructions)
        .map_err(|e| RuntimeError::Internal(format!("write TASK.md: {e}")))?;
    Ok(path)
}

/// Spawn the agent process in the workspace.
pub fn spawn_process(
    workspace: &Path,
    backend: &SpawnBackend,
    env_vars: &[(&str, &str)],
    timeout_secs: u64,
) -> RuntimeResult<SpawnedProcess> {
    let child = match backend {
        SpawnBackend::ClaudeCli { model } => {
            // Learning #7: short prompt, instructions in file
            // Learning #19: launchd has minimal PATH — resolve claude absolute path
            let claude_bin = resolve_claude_path();
            let mut cmd = Command::new("timeout");
            cmd.arg(timeout_secs.to_string());
            cmd.arg(&claude_bin);
            cmd.args(["--dangerously-skip-permissions"]);
            cmd.args(["--model", model]);
            cmd.args(["-p", "Leggi TASK.md per le istruzioni. Poi inizia."]);
            cmd.current_dir(workspace);
            for (k, v) in env_vars {
                cmd.env(k, v);
            }
            // Log output to files in worktree (Learning #18: /dev/null hides errors)
            let log_out = std::fs::File::create(workspace.join("agent.log"))
                .map_err(|e| RuntimeError::Internal(format!("create log: {e}")))?;
            let log_err = std::fs::File::create(workspace.join("agent.err"))
                .map_err(|e| RuntimeError::Internal(format!("create err: {e}")))?;
            cmd.stdin(std::process::Stdio::null());
            cmd.stdout(std::process::Stdio::from(log_out));
            cmd.stderr(std::process::Stdio::from(log_err));
            cmd.spawn()
                .map_err(|e| RuntimeError::Internal(format!("spawn claude: {e}")))?
        }
        SpawnBackend::Script { command, args } => {
            let mut cmd = Command::new("timeout");
            cmd.arg(timeout_secs.to_string());
            cmd.arg(command);
            cmd.args(args);
            cmd.current_dir(workspace);
            for (k, v) in env_vars {
                cmd.env(k, v);
            }
            let log_out = std::fs::File::create(workspace.join("agent.log"))
                .map_err(|e| RuntimeError::Internal(format!("create log: {e}")))?;
            let log_err = std::fs::File::create(workspace.join("agent.err"))
                .map_err(|e| RuntimeError::Internal(format!("create err: {e}")))?;
            cmd.stdin(std::process::Stdio::null());
            cmd.stdout(std::process::Stdio::from(log_out));
            cmd.stderr(std::process::Stdio::from(log_err));
            cmd.spawn()
                .map_err(|e| RuntimeError::Internal(format!("spawn script: {e}")))?
        }
    };

    let backend_name = match backend {
        SpawnBackend::ClaudeCli { model } => format!("claude:{model}"),
        SpawnBackend::Script { command, .. } => format!("script:{command}"),
    };

    Ok(SpawnedProcess {
        pid: child.id(),
        workspace: workspace.to_path_buf(),
        backend: backend_name,
    })
}

/// Cleanup: remove worktree after agent completes.
pub fn cleanup_worktree(repo_root: &Path, wt_path: &Path) -> RuntimeResult<()> {
    let output = Command::new("git")
        .args(["worktree", "remove", "--force"])
        .arg(wt_path)
        .current_dir(repo_root)
        .output()
        .map_err(|e| RuntimeError::Internal(format!("git worktree remove: {e}")))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        tracing::warn!("worktree cleanup failed: {stderr}");
    }
    Ok(())
}

/// Resolve the absolute path to the claude binary.
/// launchd services have a minimal PATH — "claude" alone won't be found.
fn resolve_claude_path() -> String {
    // Check env override first
    if let Ok(p) = std::env::var("CONVERGIO_CLAUDE_BIN") {
        return p;
    }
    // Common install locations
    let candidates = [
        dirs::home_dir()
            .unwrap_or_default()
            .join(".local/bin/claude"),
        dirs::home_dir()
            .unwrap_or_default()
            .join(".claude/bin/claude"),
        std::path::PathBuf::from("/usr/local/bin/claude"),
        std::path::PathBuf::from("/opt/homebrew/bin/claude"),
    ];
    for c in &candidates {
        if c.exists() {
            return c.to_string_lossy().to_string();
        }
    }
    // Fallback: hope it's in PATH
    "claude".into()
}

/// Choose backend based on model tier.
pub fn backend_for_tier(tier: &str, model: Option<&str>) -> SpawnBackend {
    match tier {
        "t1" => SpawnBackend::ClaudeCli {
            model: model.unwrap_or("claude-opus-4-6").to_string(),
        },
        "t2" => SpawnBackend::ClaudeCli {
            model: model.unwrap_or("claude-sonnet-4-6").to_string(),
        },
        "t3" => SpawnBackend::ClaudeCli {
            model: model.unwrap_or("claude-haiku-4-5").to_string(),
        },
        _ => SpawnBackend::ClaudeCli {
            model: model.unwrap_or("claude-sonnet-4-6").to_string(),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn write_instructions_creates_file() {
        let tmp = tempfile::tempdir().unwrap();
        let path = write_instructions(tmp.path(), "Test task").unwrap();
        assert!(path.exists());
        assert_eq!(fs::read_to_string(path).unwrap(), "Test task");
    }

    #[test]
    fn backend_for_tier_defaults() {
        match backend_for_tier("t1", None) {
            SpawnBackend::ClaudeCli { model } => assert!(model.contains("opus")),
            _ => panic!("expected ClaudeCli"),
        }
        match backend_for_tier("t3", None) {
            SpawnBackend::ClaudeCli { model } => assert!(model.contains("haiku")),
            _ => panic!("expected ClaudeCli"),
        }
    }

    #[test]
    fn backend_with_override() {
        match backend_for_tier("t2", Some("custom-model")) {
            SpawnBackend::ClaudeCli { model } => assert_eq!(model, "custom-model"),
            _ => panic!("expected ClaudeCli"),
        }
    }
}
