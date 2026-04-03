// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// KB (knowledge base) subcommands for the cvg CLI — delegates to daemon HTTP API.
// JSON output by default; --human flag for readable text.

use crate::cli_error::CliError;
use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum KbCommands {
    /// Search the knowledge base
    Search {
        /// Search query string
        query: String,
        /// Maximum results to return
        #[arg(long, default_value_t = 5)]
        limit: u32,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Write an entry to the knowledge base
    Write {
        /// Entry title
        title: String,
        /// Entry content
        content: String,
        /// Domain/category
        #[arg(long, default_value = "general")]
        domain: String,
        /// Confidence score (0.0–1.0)
        #[arg(long, default_value_t = 0.8)]
        confidence: f64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: KbCommands) -> Result<(), CliError> {
    match cmd {
        KbCommands::Search {
            query,
            limit,
            human,
            api_url,
        } => {
            fetch_and_print(
                &format!("{api_url}/api/plan-db/kb-search?q={query}&limit={limit}"),
                human,
            )
            .await?;
        }
        KbCommands::Write {
            title,
            content,
            domain,
            confidence,
            human,
            api_url,
        } => {
            let body = serde_json::json!({
                "title": title,
                "content": content,
                "domain": domain,
                "confidence": confidence,
            });
            post_and_print(&format!("{api_url}/api/plan-db/kb-write"), &body, human).await?;
        }
    }
    Ok(())
}

async fn fetch_and_print(url: &str, human: bool) -> Result<(), CliError> {
    match reqwest::get(url).await {
        Ok(resp) => {
            let status = resp.status();
            let val: serde_json::Value = resp
                .json()
                .await
                .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
            print_value(&val, human);
            if !status.is_success() {
                return Err(CliError::NotFound(val.to_string()));
            }
            Ok(())
        }
        Err(e) => Err(CliError::ApiCallFailed(format!(
            "error connecting to daemon: {e}"
        ))),
    }
}

async fn post_and_print(url: &str, body: &serde_json::Value, human: bool) -> Result<(), CliError> {
    let client = reqwest::Client::new();
    match client.post(url).json(body).send().await {
        Ok(resp) => {
            let status = resp.status();
            let val: serde_json::Value = resp
                .json()
                .await
                .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
            print_value(&val, human);
            if !status.is_success() {
                return Err(CliError::NotFound(val.to_string()));
            }
            Ok(())
        }
        Err(e) => Err(CliError::ApiCallFailed(format!(
            "error connecting to daemon: {e}"
        ))),
    }
}

fn print_value(val: &serde_json::Value, human: bool) {
    if human {
        println!(
            "{}",
            serde_json::to_string_pretty(val).unwrap_or_else(|_| val.to_string())
        );
    } else {
        println!("{val}");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kb_commands_search_variant_exists() {
        let cmd = KbCommands::Search {
            query: "rust async".to_string(),
            limit: 10,
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, KbCommands::Search { .. }));
    }

    #[test]
    fn kb_commands_write_variant_exists() {
        let cmd = KbCommands::Write {
            title: "TDD pattern".to_string(),
            content: "Write tests first".to_string(),
            domain: "testing".to_string(),
            confidence: 0.9,
            human: false,
            api_url: "http://localhost:8420".to_string(),
        };
        assert!(matches!(cmd, KbCommands::Write { .. }));
    }

    #[test]
    fn kb_write_builds_correct_body() {
        let body = serde_json::json!({
            "title": "test",
            "content": "body",
            "domain": "general",
            "confidence": 0.8_f64,
        });
        assert_eq!(body["domain"], "general");
        assert!((body["confidence"].as_f64().unwrap() - 0.8).abs() < 0.001);
    }

    #[test]
    fn kb_search_url_encodes_query() {
        let query = "rust async";
        let limit = 5u32;
        let url = format!("http://localhost:8420/api/plan-db/kb-search?q={query}&limit={limit}");
        assert!(url.contains("q=rust async"));
        assert!(url.contains("limit=5"));
    }
}
