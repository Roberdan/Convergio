// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Lock subcommand — acquire/release/list file locks via daemon HTTP API.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum LockCommands {
    /// Acquire a file lock for a task
    Acquire {
        /// File path to lock
        file_path: String,
        /// Task DB ID that owns this lock
        task_id: i64,
        /// Agent identifier
        #[arg(long, default_value = "task-executor")]
        agent: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Release a file lock
    Release {
        /// File path to unlock
        file_path: String,
        /// Task DB ID releasing this lock
        task_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// List all active file locks
    List {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: LockCommands) {
    match cmd {
        LockCommands::Acquire {
            file_path,
            task_id,
            agent,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "file_path": file_path, "task_id": task_id, "agent": agent,
            });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/ipc/locks/acquire"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        LockCommands::Release {
            file_path,
            task_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({ "file_path": file_path, "task_id": task_id });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/ipc/locks/release"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        LockCommands::List { human, api_url } => {
            if let Err(e) =
                crate::cli_http::fetch_and_print(&format!("{api_url}/api/ipc/locks"), human).await
            {
                eprintln!("error: {e}");
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lock_acquire_variant_exists() {
        let cmd = LockCommands::Acquire {
            file_path: "daemon/src/main.rs".to_string(),
            task_id: 8796,
            agent: "task-executor".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, LockCommands::Acquire { task_id: 8796, .. }));
    }

    #[test]
    fn lock_release_variant_exists() {
        let cmd = LockCommands::Release {
            file_path: "daemon/src/main.rs".to_string(),
            task_id: 8796,
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, LockCommands::Release { task_id: 8796, .. }));
    }

    #[test]
    fn lock_list_variant_exists() {
        let cmd = LockCommands::List {
            human: true,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, LockCommands::List { human: true, .. }));
    }

    #[test]
    fn lock_acquire_body_shape() {
        let body = serde_json::json!({
            "file_path": "daemon/src/main.rs",
            "task_id": 8796_i64,
            "agent": "task-executor",
        });
        assert_eq!(body["task_id"], 8796);
        assert_eq!(body["agent"], "task-executor");
    }
}
