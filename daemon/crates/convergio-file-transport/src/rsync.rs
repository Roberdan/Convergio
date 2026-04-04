//! Rsync wrapper — builds and executes rsync commands for file transfer.

use crate::types::{TransferDirection, TransferRequest, TransferResult, TransferStatus};
use std::time::Instant;
use tokio::process::Command;

/// Build the rsync command for a given transfer request.
///
/// Push: `rsync -avz --delete -e ssh source user@host:dest`
/// Pull: `rsync -avz --delete -e ssh user@host:source dest`
pub fn build_rsync_command(req: &TransferRequest, ssh_target: &str) -> Command {
    let mut cmd = Command::new("rsync");
    cmd.args(["-avz", "--delete", "-e", "ssh"]);

    for pattern in &req.exclude_patterns {
        cmd.arg(format!("--exclude={pattern}"));
    }

    match req.direction {
        TransferDirection::Push => {
            cmd.arg(&req.source_path);
            cmd.arg(format!("{ssh_target}:{}", req.dest_path));
        }
        TransferDirection::Pull => {
            cmd.arg(format!("{ssh_target}:{}", req.source_path));
            cmd.arg(&req.dest_path);
        }
    }

    cmd
}

/// Execute rsync and parse the output for transfer statistics.
pub async fn execute_rsync(
    req: &TransferRequest,
    ssh_target: &str,
) -> Result<TransferResult, Box<dyn std::error::Error + Send + Sync>> {
    let start = Instant::now();
    let mut cmd = build_rsync_command(req, ssh_target);

    let output = cmd.output().await?;
    let duration_ms = start.elapsed().as_millis() as u64;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if !output.status.success() {
        let msg = if stderr.is_empty() {
            format!("rsync exit code {}", output.status)
        } else {
            stderr.trim().to_string()
        };
        return Ok(TransferResult {
            peer_name: req.peer_name.clone(),
            bytes_transferred: 0,
            files_count: 0,
            duration_ms,
            status: TransferStatus::Failed(msg),
        });
    }

    let (bytes, files) = parse_rsync_output(&stdout);
    Ok(TransferResult {
        peer_name: req.peer_name.clone(),
        bytes_transferred: bytes,
        files_count: files,
        duration_ms,
        status: TransferStatus::Success,
    })
}

/// Parse rsync summary output for bytes transferred and file count.
///
/// Rsync outputs lines like:
///   "sent 1,234 bytes  received 56 bytes"
///   "total size is 5,678  speedup is 1.23"
/// and lists transferred files one per line before the summary.
pub fn parse_rsync_output(output: &str) -> (u64, u64) {
    let mut bytes: u64 = 0;
    let mut files: u64 = 0;

    for line in output.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("sent ") && trimmed.contains("bytes") {
            // "sent 1,234 bytes  received 56 bytes  ..."
            if let Some(val) = extract_number_after(trimmed, "sent ") {
                bytes += val;
            }
        } else if trimmed.starts_with("total size is ") {
            // Ignore — we use sent bytes as the metric
        } else if !trimmed.is_empty()
            && !trimmed.starts_with("receiving")
            && !trimmed.starts_with("sending")
            && !trimmed.starts_with("created directory")
            && !trimmed.starts_with("./")
            && !trimmed.contains("speedup is")
            && !trimmed.contains("bytes/sec")
        {
            // Count non-header lines as transferred files
            files += 1;
        }
    }

    (bytes, files)
}

/// Extract a number (with commas stripped) following a prefix in a line.
fn extract_number_after(line: &str, prefix: &str) -> Option<u64> {
    let rest = line.strip_prefix(prefix)?;
    let num_str: String = rest
        .chars()
        .take_while(|c| c.is_ascii_digit() || *c == ',')
        .collect();
    num_str.replace(',', "").parse().ok()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_request(dir: TransferDirection) -> TransferRequest {
        TransferRequest {
            source_path: "/data/project/".into(),
            dest_path: "/backup/project/".into(),
            peer_name: "studio-mac".into(),
            ssh_target: "rob@192.168.1.50".into(),
            direction: dir,
            exclude_patterns: vec![],
        }
    }

    #[test]
    fn build_rsync_command_push() {
        let req = sample_request(TransferDirection::Push);
        let cmd = build_rsync_command(&req, "rob@192.168.1.50");
        let prog = cmd.as_std().get_program().to_str().unwrap();
        assert_eq!(prog, "rsync");
        let args: Vec<_> = cmd
            .as_std()
            .get_args()
            .map(|a| a.to_str().unwrap())
            .collect();
        assert!(args.contains(&"-avz"));
        assert!(args.contains(&"--delete"));
        assert!(args.contains(&"/data/project/"));
        assert!(args.contains(&"rob@192.168.1.50:/backup/project/"));
    }

    #[test]
    fn build_rsync_command_pull() {
        let req = sample_request(TransferDirection::Pull);
        let cmd = build_rsync_command(&req, "rob@192.168.1.50");
        let args: Vec<_> = cmd
            .as_std()
            .get_args()
            .map(|a| a.to_str().unwrap())
            .collect();
        assert!(args.contains(&"rob@192.168.1.50:/data/project/"));
        assert!(args.contains(&"/backup/project/"));
    }

    #[test]
    fn build_rsync_with_excludes() {
        let mut req = sample_request(TransferDirection::Push);
        req.exclude_patterns = vec!["*.tmp".into(), ".git".into()];
        let cmd = build_rsync_command(&req, "rob@192.168.1.50");
        let args: Vec<_> = cmd
            .as_std()
            .get_args()
            .map(|a| a.to_str().unwrap())
            .collect();
        assert!(args.contains(&"--exclude=*.tmp"));
        assert!(args.contains(&"--exclude=.git"));
    }

    #[test]
    fn parse_rsync_output_extracts_stats() {
        let output = "\
file1.txt
file2.txt
sent 1,234 bytes  received 56 bytes  2,580.00 bytes/sec
total size is 5,678  speedup is 4.40";
        let (bytes, files) = parse_rsync_output(output);
        assert_eq!(bytes, 1234);
        assert_eq!(files, 2);
    }

    #[test]
    fn parse_rsync_output_empty() {
        let (bytes, files) = parse_rsync_output("");
        assert_eq!(bytes, 0);
        assert_eq!(files, 0);
    }
}
