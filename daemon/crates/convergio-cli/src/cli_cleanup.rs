// cvg cleanup — find and remove stale worktree branches and orphan worktrees.
// Cleans up worktree-agent-*, worktree-plan-*, wt-plan-* branches without matching dirs.

use crate::cli_error::CliError;
use std::collections::HashSet;

pub async fn handle() -> Result<(), CliError> {
    let active_paths = list_active_worktree_paths();
    let stale_branches = find_stale_branches(&active_paths);

    if stale_branches.is_empty() {
        println!("No stale worktree branches found.");
    } else {
        println!("Found {} stale branch(es):", stale_branches.len());
        for b in &stale_branches {
            println!("  - {b}");
        }
        delete_branches(&stale_branches);
    }

    // Always prune worktree metadata for removed directories
    prune_worktrees();
    Ok(())
}

/// List paths of active git worktrees (from `git worktree list --porcelain`).
fn list_active_worktree_paths() -> HashSet<String> {
    let out = match std::process::Command::new("git")
        .args(["worktree", "list", "--porcelain"])
        .output()
    {
        Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).to_string(),
        _ => return HashSet::new(),
    };
    out.lines()
        .filter_map(|line| line.strip_prefix("worktree "))
        .map(String::from)
        .collect()
}

/// Pure filtering logic extracted from find_stale_branches for unit-testability.
/// Takes `branch_lines` as the raw output of `git branch --list`.
fn classify_stale_branches(active_paths: &HashSet<String>, branch_lines: &str) -> Vec<String> {
    let prefixes = [
        "worktree-agent-",
        "worktree-plan-",
        "wt-plan-",
        "workspace/ws-",
    ];
    let mut stale = Vec::new();
    for line in branch_lines.lines() {
        let branch = line.trim().trim_start_matches("* ");
        if !prefixes.iter().any(|p| branch.starts_with(p) || branch.contains(p)) {
            continue;
        }
        let has_active = active_paths.iter().any(|p| {
            p.contains(&branch.replace('/', "-")) || p.contains(branch)
        });
        if !has_active {
            stale.push(branch.to_string());
        }
    }
    stale
}

/// Find branches matching worktree patterns that have no active worktree directory.
fn find_stale_branches(active_paths: &HashSet<String>) -> Vec<String> {
    let out = match std::process::Command::new("git")
        .args(["branch", "--list"])
        .output()
    {
        Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).to_string(),
        _ => return Vec::new(),
    };
    classify_stale_branches(active_paths, &out)
}

fn delete_branches(branches: &[String]) {
    for branch in branches {
        let out = std::process::Command::new("git")
            .args(["branch", "-D", branch])
            .output();
        match out {
            Ok(o) if o.status.success() => {
                println!("  deleted branch: {branch}");
            }
            Ok(o) => {
                let err = String::from_utf8_lossy(&o.stderr);
                eprintln!("  failed to delete {branch}: {err}");
            }
            Err(e) => {
                eprintln!("  git branch -D {branch}: {e}");
            }
        }
    }
}

fn prune_worktrees() {
    match std::process::Command::new("git")
        .args(["worktree", "prune"])
        .output()
    {
        Ok(o) if o.status.success() => {
            println!("Worktree metadata pruned.");
        }
        Ok(o) => {
            let err = String::from_utf8_lossy(&o.stderr);
            eprintln!("worktree prune failed: {err}");
        }
        Err(e) => {
            eprintln!("worktree prune: {e}");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stale_branch_no_active_paths_marks_all_matching_as_stale() {
        let active: HashSet<String> = HashSet::new();
        let lines = "  worktree-plan-42\n  worktree-agent-x\n  main\n";
        let stale = classify_stale_branches(&active, lines);
        assert!(stale.contains(&"worktree-plan-42".to_string()), "plan-42 should be stale");
        assert!(stale.contains(&"worktree-agent-x".to_string()), "agent-x should be stale");
        // "main" does not match any worktree prefix — must not appear
        assert!(!stale.contains(&"main".to_string()), "main is not a worktree branch");
    }

    #[test]
    fn stale_branch_active_path_protects_matching_branch() {
        let mut active: HashSet<String> = HashSet::new();
        active.insert("/work/worktree-plan-42".to_string());
        let lines = "  worktree-plan-42\n  worktree-plan-99\n";
        let stale = classify_stale_branches(&active, lines);
        // plan-42 has an active worktree directory — NOT stale
        assert!(!stale.contains(&"worktree-plan-42".to_string()), "plan-42 has active worktree");
        // plan-99 has no active directory — stale
        assert!(stale.contains(&"worktree-plan-99".to_string()), "plan-99 should be stale");
    }

    #[test]
    fn stale_branch_empty_input_returns_empty() {
        let active: HashSet<String> = HashSet::new();
        let stale = classify_stale_branches(&active, "");
        assert!(stale.is_empty(), "no branches → no stale branches");
    }

    #[test]
    fn stale_branch_current_branch_marker_stripped() {
        // `git branch --list` prefixes the active branch with "* "
        let active: HashSet<String> = HashSet::new();
        let lines = "* worktree-plan-1\n  wt-plan-2\n";
        let stale = classify_stale_branches(&active, lines);
        assert!(stale.contains(&"worktree-plan-1".to_string()), "current branch marker stripped");
        assert!(stale.contains(&"wt-plan-2".to_string()));
    }
}
