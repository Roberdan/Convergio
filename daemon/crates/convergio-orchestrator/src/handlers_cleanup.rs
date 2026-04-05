//! Worktree cleanup — removes worktrees and branches when a plan completes.
//!
//! Called from on_plan_done(). Runs as a background tokio task (fire-and-forget).
//! Only cleans up agents in terminal stages (stopped, reaped, failed).

use convergio_db::pool::ConnPool;
use std::path::Path;
use std::process::Command;

/// Trigger cleanup for all agents that worked on this plan.
/// Non-blocking: spawns a background task.
pub fn cleanup_plan_worktrees(pool: ConnPool, plan_id: i64) {
    tokio::spawn(async move {
        if let Err(e) = do_cleanup(&pool, plan_id) {
            tracing::warn!(plan_id, error = %e, "worktree cleanup failed");
        }
    });
}

fn do_cleanup(pool: &ConnPool, plan_id: i64) -> Result<(), Box<dyn std::error::Error>> {
    let conn = pool.get()?;

    // Find agents that worked on tasks in this plan and are in terminal stage
    let mut stmt = conn.prepare(
        "SELECT a.id, a.workspace_path FROM art_agents a \
         JOIN tasks t ON a.task_id = t.id \
         WHERE t.plan_id = ?1 \
         AND a.stage IN ('stopped', 'reaped', 'failed') \
         AND a.workspace_path IS NOT NULL",
    )?;

    let agents: Vec<(String, String)> = stmt
        .query_map(rusqlite::params![plan_id], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })?
        .filter_map(|r| r.ok())
        .collect();

    if agents.is_empty() {
        tracing::debug!(plan_id, "no worktrees to clean up");
        return Ok(());
    }

    // Find repo root (parent of .worktrees)
    let repo_root = find_repo_root(&agents[0].1);

    let mut cleaned = 0usize;
    for (agent_id, ws_path) in &agents {
        let path = Path::new(ws_path);
        if !path.exists() {
            tracing::debug!(agent_id = agent_id.as_str(), "worktree already gone");
            cleaned += 1;
            continue;
        }

        // Get branch name before removing worktree
        let branch = get_branch(path);

        // Remove worktree
        if let Some(ref root) = repo_root {
            remove_worktree(root, path);
        }

        // Delete branch if merged
        if let Some(ref b) = branch {
            delete_merged_branch(b, repo_root.as_deref());
        }

        // Mark workspace as cleaned in DB
        let _ = conn.execute(
            "UPDATE art_agents SET workspace_path = NULL, \
             updated_at = datetime('now') WHERE id = ?1",
            rusqlite::params![agent_id],
        );

        cleaned += 1;
    }

    // Prune worktree metadata
    if let Some(ref root) = repo_root {
        let _ = Command::new("git")
            .args(["worktree", "prune"])
            .current_dir(root)
            .output();
    }

    tracing::info!(
        plan_id,
        cleaned,
        total = agents.len(),
        "worktree cleanup complete"
    );
    Ok(())
}

fn find_repo_root(ws_path: &str) -> Option<String> {
    // Worktree paths are <repo>/.worktrees/<name>, so repo root is 2 levels up
    let path = Path::new(ws_path);
    path.parent()
        .and_then(|p| p.parent())
        .map(|p| p.to_string_lossy().to_string())
}

fn get_branch(workspace: &Path) -> Option<String> {
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

fn remove_worktree(repo_root: &str, ws_path: &Path) {
    let output = Command::new("git")
        .args(["worktree", "remove", "--force"])
        .arg(ws_path)
        .current_dir(repo_root)
        .output();
    match output {
        Ok(o) if o.status.success() => {
            tracing::debug!(path = %ws_path.display(), "worktree removed");
        }
        Ok(o) => {
            let err = String::from_utf8_lossy(&o.stderr);
            tracing::warn!(path = %ws_path.display(), "worktree remove failed: {err}");
        }
        Err(e) => {
            tracing::warn!(path = %ws_path.display(), "git worktree remove: {e}");
        }
    }
}

fn delete_merged_branch(branch: &str, repo_root: Option<&str>) {
    let cwd = repo_root.unwrap_or(".");

    // Check if branch is merged into main
    let merged = Command::new("git")
        .args(["branch", "--merged", "main"])
        .current_dir(cwd)
        .output()
        .ok()
        .map(|o| {
            String::from_utf8_lossy(&o.stdout)
                .lines()
                .any(|l| l.trim().trim_start_matches("* ") == branch)
        })
        .unwrap_or(false);

    if !merged {
        tracing::debug!(branch, "branch not merged — skipping delete");
        return;
    }

    // Delete local branch
    let _ = Command::new("git")
        .args(["branch", "-d", branch])
        .current_dir(cwd)
        .output();

    // Delete remote branch
    let _ = Command::new("git")
        .args(["push", "origin", "--delete", branch])
        .current_dir(cwd)
        .output();

    tracing::debug!(branch, "merged branch deleted (local + remote)");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn find_repo_root_extracts_parent() {
        let root = find_repo_root("/home/user/project/.worktrees/agent-x");
        assert_eq!(root, Some("/home/user/project".to_string()));
    }

    #[test]
    fn find_repo_root_handles_nested() {
        let root = find_repo_root("/a/b/.worktrees/w1");
        assert_eq!(root, Some("/a/b".to_string()));
    }
}
