// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Bus (IPC) subcommands for the cvg CLI — delegates to daemon HTTP API.
// JSON output by default; --human flag for readable text.

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum BusCommands {
    /// List connected agents on the IPC bus
    Who {
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Send a message to a specific agent
    Send {
        /// Sender agent name
        from: String,
        /// Recipient agent name
        to: String,
        /// Message content
        message: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Read messages for an agent
    Read {
        /// Agent name to read messages for
        name: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Broadcast a message to all agents
    Broadcast {
        /// Sender agent name
        from: String,
        /// Message content
        message: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Render org hierarchy tree from org API data
    Org {
        /// Human-readable tree output (default true)
        #[arg(long, default_value_t = true)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Watch direct messages for an agent over SSE
    Watch {
        /// Agent name to subscribe as
        name: String,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Ask an agent and wait for a direct reply
    Ask {
        /// Sender agent name
        from: String,
        /// Recipient agent name
        to: String,
        /// Message content
        message: String,
        /// Timeout in seconds
        #[arg(long, default_value_t = 120)]
        timeout: u64,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: BusCommands) {
    match cmd {
        BusCommands::Who { human, api_url } => {
            if let Err(e) = crate::cli_http::fetch_and_print(&format!("{api_url}/api/ipc/agents"), human).await {
                eprintln!("error: {e}");
            }
        }
        BusCommands::Send {
            from,
            to,
            message,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "from": from,
                "to": to,
                "message": message,
            });
            if let Err(e) = crate::cli_http::post_and_print(&format!("{api_url}/api/ipc/send"), &body, human).await {
                eprintln!("error: {e}");
            }
        }
        BusCommands::Read {
            name,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/ipc/messages?agent={name}"),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        BusCommands::Broadcast {
            from,
            message,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "from": from,
                "message": message,
            });
            if let Err(e) = crate::cli_http::post_and_print(&format!("{api_url}/api/ipc/broadcast"), &body, human)
                .await
            {
                eprintln!("error: {e}");
            }
        }
        BusCommands::Org { human, api_url } => {
            crate::cli_bus_org::run_org(&api_url, human).await;
        }
        BusCommands::Watch { name, api_url } => {
            if let Err(e) = crate::cli_bus_watch::run_watch(&name, &api_url).await {
                eprintln!("error: {e}");
            }
        }
        BusCommands::Ask {
            from,
            to,
            message,
            timeout,
            api_url,
        } => {
            crate::cli_bus_ask::run_ask(&from, &to, &message, timeout, &api_url).await;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bus_who_variant_exists() {
        let cmd = BusCommands::Who {
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BusCommands::Who { .. }));
    }

    #[test]
    fn bus_send_variant_exists() {
        let cmd = BusCommands::Send {
            from: "planner".to_string(),
            to: "executor".to_string(),
            message: "start task T1-01".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BusCommands::Send { .. }));
    }

    #[test]
    fn bus_send_body_shape() {
        let body = serde_json::json!({
            "from": "planner",
            "to": "executor",
            "message": "start task T1-01",
        });
        assert_eq!(body["from"], "planner");
        assert_eq!(body["to"], "executor");
        assert_eq!(body["message"], "start task T1-01");
    }

    #[test]
    fn bus_read_variant_exists() {
        let cmd = BusCommands::Read {
            name: "thor".to_string(),
            human: true,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BusCommands::Read { .. }));
    }

    #[test]
    fn bus_broadcast_variant_exists() {
        let cmd = BusCommands::Broadcast {
            from: "coordinator".to_string(),
            message: "wave complete".to_string(),
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BusCommands::Broadcast { .. }));
    }

    #[test]
    fn bus_broadcast_body_shape() {
        let body = serde_json::json!({
            "from": "coordinator",
            "message": "wave complete",
        });
        assert_eq!(body["from"], "coordinator");
        assert_eq!(body["message"], "wave complete");
    }

    #[test]
    fn bus_read_url_includes_agent_param() {
        let name = "thor";
        let api_url = "http://localhost:8420";
        let url = format!("{api_url}/api/ipc/messages?agent={name}");
        assert!(url.contains("agent=thor"));
    }

    #[test]
    fn bus_org_variant_exists() {
        let cmd = BusCommands::Org {
            human: true,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, BusCommands::Org { .. }));
    }
}
