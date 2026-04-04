//! SSH-based remote agent spawning on mesh peers.

use tokio::process::Command;

type BoxErr = Box<dyn std::error::Error + Send + Sync>;

/// Spawn an agent on a remote peer via SSH + tmux.
///
/// Connects to the peer, changes to the project directory, and starts
/// a new tmux window running the claude CLI with auto-execution.
pub async fn spawn_on_peer(
    ssh_target: &str,
    remote_path: &str,
    plan_id: i64,
    tmux_session: &str,
    tmux_window: &str,
) -> Result<(), BoxErr> {
    let mut cmd = build_ssh_command(ssh_target, remote_path, plan_id, tmux_session, tmux_window);
    tracing::info!(
        ssh_target,
        remote_path,
        plan_id,
        tmux_session,
        tmux_window,
        "spawning remote agent"
    );

    let output = cmd.output().await?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let msg = if stderr.is_empty() {
            format!("SSH exit code {}", output.status)
        } else {
            stderr.trim().to_string()
        };
        tracing::error!(ssh_target, error = %msg, "remote spawn failed");
        return Err(msg.into());
    }

    tracing::info!(
        ssh_target,
        tmux_session,
        tmux_window,
        "remote agent spawned"
    );
    Ok(())
}

/// Build the SSH command for remote agent spawning (exposed for testing).
pub fn build_ssh_command(
    ssh_target: &str,
    remote_path: &str,
    _plan_id: i64,
    tmux_session: &str,
    tmux_window: &str,
) -> Command {
    let remote_cmd = format!(
        "cd {remote_path} && tmux new-window -t {tmux_session} -n {tmux_window} \
         'claude --dangerously-skip-permissions \
         -p \"Read TASK.md and execute\" --max-turns 50'"
    );
    let mut cmd = Command::new("ssh");
    cmd.arg(ssh_target).arg(remote_cmd);
    cmd
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn build_ssh_command_format() {
        let cmd = build_ssh_command("rob@studio-mac", "/tmp/project", 42, "cvg-del", "plan-42");
        let prog = cmd.as_std().get_program().to_str().unwrap();
        assert_eq!(prog, "ssh");

        let args: Vec<_> = cmd
            .as_std()
            .get_args()
            .map(|a| a.to_str().unwrap().to_string())
            .collect();
        assert_eq!(args[0], "rob@studio-mac");
        assert!(args[1].contains("cd /tmp/project"));
        assert!(args[1].contains("tmux new-window"));
        assert!(args[1].contains("-t cvg-del"));
        assert!(args[1].contains("-n plan-42"));
        assert!(args[1].contains("claude --dangerously-skip-permissions"));
        assert!(args[1].contains("--max-turns 50"));
    }

    #[test]
    fn build_ssh_command_with_alias() {
        let cmd = build_ssh_command("studio-mac", "/data/work", 7, "sess", "win");
        let args: Vec<_> = cmd
            .as_std()
            .get_args()
            .map(|a| a.to_str().unwrap().to_string())
            .collect();
        assert_eq!(args[0], "studio-mac");
        assert!(args[1].contains("cd /data/work"));
    }
}
