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
        // Sentinel watcher: kill agent on STOP signal
        let ws_clone = workspace.clone();
        let sentinel_handle = tokio::spawn(async move {
            loop {
                tokio::time::sleep(std::time::Duration::from_secs(10)).await;
                if let Some(s) = crate::adaptation::check_sentinel(&ws_clone) {
                    if s == "STOP" {
                        tracing::info!(pid, "STOP sentinel detected, killing agent");
                        unsafe {
                            libc::kill(pid as i32, libc::SIGTERM);
                        }
                        break;
                    }
                }
            }
        });
        // Wait for process to exit (poll every 5s)
        let exited = wait_for_exit(pid).await;
        sentinel_handle.abort();
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
            // Update plan task status if agent was working on a plan task
            update_plan_task(&pool, &agent_id, "submitted");
        } else {
            // Agent failed — mark task as failed too
            update_plan_task(&pool, &agent_id, "failed");
        }

        // Auto-respawn if checkpoint exists
        if stage == "stopped" || stage == "failed" {
            let repo = std::env::current_dir()
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_else(|_| ".".into());
            let daemon = std::env::var("CONVERGIO_DAEMON_URL")
                .unwrap_or_else(|_| "http://localhost:8420".into());
            match crate::respawn::try_respawn(&pool, &agent_id, &daemon, &repo) {
                Ok(Some(new_id)) => {
                    tracing::info!(
                        agent_id = agent_id.as_str(),
                        new = new_id.as_str(),
                        "continuation spawned"
                    );
                }
                Ok(None) => tracing::debug!(agent_id = agent_id.as_str(), "no respawn needed"),
                Err(e) => {
                    tracing::warn!(agent_id = agent_id.as_str(), error = %e, "respawn failed")
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
        let result = unsafe { libc::waitpid(pid as i32, &mut status, libc::WNOHANG) };
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
    crate::monitor_helpers::read_tail(path, lines)
}

fn resolve_gh_path() -> String {
    crate::monitor_helpers::resolve_gh_path()
}

#[path = "plan_task_update.rs"]
mod plan_task_update;
use plan_task_update::update_plan_task;
