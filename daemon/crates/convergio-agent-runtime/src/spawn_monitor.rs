//! Spawn monitor — watches agent processes, handles completion.
//!
//! When an agent process exits:
//! 1. Read exit code and agent.log
//! 2. Check if agent committed (git log)
//! 3. If committed: push branch + create PR via gh
//! 4. Update agent stage in DB (stopped/failed)
//! 5. Notify via domain event sink (SSE → UI, Telegram if configured)

use std::path::Path;
use std::process::Command;

use convergio_db::pool::ConnPool;
use tokio::task::JoinHandle;

/// Track a spawned agent process. Returns a JoinHandle for the monitor task.
pub fn monitor_agent(
    pool: ConnPool,
    agent_id: String,
    pid: u32,
    workspace: String,
    _repo_root: String,
) -> JoinHandle<()> {
    tokio::spawn(async move {
        // Wait for process to exit (poll every 5s)
        let exited = wait_for_exit(pid).await;
        tracing::info!(
            agent_id = agent_id.as_str(),
            pid,
            exit = exited,
            "agent process exited"
        );

        let ws = Path::new(&workspace);

        // Check if agent committed
        let committed = has_new_commits(ws);
        let branch = get_branch_name(ws);

        // Read log tail
        let _log_tail = read_tail(&ws.join("agent.log"), 20);
        let err_tail = read_tail(&ws.join("agent.err"), 10);

        // Update DB: mark as stopped or failed
        let stage = if committed { "stopped" } else { "failed" };
        if let Ok(conn) = pool.get() {
            let _ = conn.execute(
                "UPDATE art_agents SET stage = ?1, updated_at = datetime('now') WHERE id = ?2",
                rusqlite::params![stage, agent_id],
            );
        }

        // If committed: push + create PR
        if committed {
            if let Some(ref branch) = branch {
                let push_ok = push_branch(ws, branch);
                if push_ok {
                    let pr_url = create_pr(ws, branch);
                    tracing::info!(
                        agent_id = agent_id.as_str(),
                        branch,
                        pr = pr_url.as_deref().unwrap_or("failed"),
                        "agent work pushed"
                    );
                }
            }
        }

        // Log summary
        if !err_tail.is_empty() {
            tracing::warn!(agent_id = agent_id.as_str(), "agent stderr:\n{err_tail}");
        }
        tracing::info!(
            agent_id = agent_id.as_str(),
            committed,
            stage,
            "agent monitor complete"
        );
    })
}

/// Poll until process exits. Returns exit code or -1.
/// Uses waitpid(WNOHANG) to detect zombie processes that kill(0) misses.
async fn wait_for_exit(pid: u32) -> i32 {
    loop {
        tokio::time::sleep(std::time::Duration::from_secs(5)).await;
        // Try waitpid first — catches zombies that kill(0) reports as alive
        let mut status: i32 = 0;
        let result =
            unsafe { libc::waitpid(pid as i32, &mut status, libc::WNOHANG) };
        if result > 0 {
            // Process exited (or was zombie, now reaped)
            if libc::WIFEXITED(status) {
                return libc::WEXITSTATUS(status);
            }
            return -1;
        }
        // waitpid returns 0 = still running, -1 = not our child
        if result < 0 {
            // ECHILD: not our child process (already reaped or not a child)
            let alive = unsafe { libc::kill(pid as i32, 0) } == 0;
            if !alive {
                return -1;
            }
        }
    }
}

/// Check if the agent made commits beyond the base.
fn has_new_commits(workspace: &Path) -> bool {
    // Check if HEAD differs from origin/main
    let output = Command::new("git")
        .args(["log", "--oneline", "origin/main..HEAD"])
        .current_dir(workspace)
        .output();
    match output {
        Ok(o) => {
            let stdout = String::from_utf8_lossy(&o.stdout);
            !stdout.trim().is_empty()
        }
        Err(_) => false,
    }
}

/// Get current branch name.
fn get_branch_name(workspace: &Path) -> Option<String> {
    Command::new("git")
        .args(["branch", "--show-current"])
        .current_dir(workspace)
        .output()
        .ok()
        .and_then(|o| {
            let name = String::from_utf8_lossy(&o.stdout).trim().to_string();
            if name.is_empty() {
                None
            } else {
                Some(name)
            }
        })
}

/// Push the current branch to origin.
fn push_branch(workspace: &Path, branch: &str) -> bool {
    let output = Command::new("git")
        .args(["push", "-u", "origin", branch])
        .current_dir(workspace)
        .output();
    match output {
        Ok(o) if o.status.success() => true,
        Ok(o) => {
            let stderr = String::from_utf8_lossy(&o.stderr);
            tracing::warn!("git push failed: {stderr}");
            false
        }
        Err(e) => {
            tracing::warn!("git push error: {e}");
            false
        }
    }
}

/// Create a PR via gh CLI.
fn create_pr(workspace: &Path, branch: &str) -> Option<String> {
    let gh = resolve_gh_path();
    let title = format!("feat: agent work on {branch}");
    let output = Command::new(&gh)
        .args([
            "pr",
            "create",
            "--base",
            "main",
            "--title",
            &title,
            "--body",
            "Produced by convergio agent.\n\n🤖 Generated with convergio daemon",
        ])
        .current_dir(workspace)
        .output()
        .ok()?;
    if output.status.success() {
        let url = String::from_utf8_lossy(&output.stdout).trim().to_string();
        Some(url)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        tracing::warn!("gh pr create failed: {stderr}");
        None
    }
}

fn read_tail(path: &Path, lines: usize) -> String {
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

/// Resolve gh CLI path (same issue as claude — launchd minimal PATH).
fn resolve_gh_path() -> String {
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
