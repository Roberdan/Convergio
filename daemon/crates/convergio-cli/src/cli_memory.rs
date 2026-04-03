use crate::cli_error::CliError;
use clap::Subcommand;

const DEFAULT_API: &str = "http://127.0.0.1:8420";

#[derive(Debug, Subcommand)]
pub enum MemoryCommands {
    /// Store a new memory (cvg memory remember "content" --agent <id> --type Fact)
    Remember {
        content: String,
        #[arg(long)]
        agent: String,
        #[arg(long, default_value = "Fact")]
        r#type: String,
        #[arg(long, value_delimiter = ',')]
        tags: Option<Vec<String>>,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Recall memories (cvg memory recall --query "search" --limit 10)
    Recall {
        #[arg(long)]
        query: Option<String>,
        #[arg(long)]
        semantic: Option<String>,
        #[arg(long)]
        r#type: Option<String>,
        #[arg(long)]
        agent: Option<String>,
        #[arg(long, default_value = "10")]
        limit: usize,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
        #[arg(long)]
        human: bool,
    },
    /// Forget a memory by ID (cvg memory forget <id>)
    Forget {
        id: String,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Share a memory with other agents (cvg memory share <id> --to agent1,agent2)
    Share {
        id: String,
        #[arg(long, value_delimiter = ',')]
        to: Vec<String>,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Attest a memory (cvg memory attest <id> --agent <id> --confidence 0.95)
    Attest {
        id: String,
        #[arg(long)]
        agent: String,
        #[arg(long, default_value = "1.0")]
        confidence: f64,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Export all memories as Markdown files (cvg memory export --dir <path>)
    Export {
        #[arg(long)]
        dir: String,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
    /// Rebuild indexes: Markdown → SQLite → VectorStore (cvg memory reindex)
    Reindex {
        /// Directory with Markdown memory files
        #[arg(long)]
        dir: Option<String>,
        #[arg(long, default_value = DEFAULT_API)]
        api_url: String,
    },
}

pub async fn handle(cmd: MemoryCommands) -> Result<(), CliError> {
    match cmd {
        MemoryCommands::Remember {
            content,
            agent,
            r#type,
            tags,
            api_url,
        } => {
            let body = serde_json::json!({
                "agent_id": agent,
                "memory_type": r#type,
                "content": content,
                "tags": tags.unwrap_or_default(),
                "access_level": "Private"
            });
            let url = format!("{api_url}/api/memory/remember");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        MemoryCommands::Recall {
            query,
            semantic,
            r#type,
            agent,
            limit,
            api_url,
            human,
        } => {
            let mut params = vec![format!("limit={limit}")];
            if let Some(q) = query {
                params.push(format!("query={q}"));
            }
            if let Some(s) = semantic {
                params.push(format!("semantic={s}"));
            }
            if let Some(t) = r#type {
                params.push(format!("type={t}"));
            }
            if let Some(a) = agent {
                params.push(format!("agent={a}"));
            }
            let qs = params.join("&");
            crate::cli_http::fetch_and_print(&format!("{api_url}/api/memory/recall?{qs}"), human)
                .await
        }
        MemoryCommands::Forget { id, api_url } => {
            let url = format!("{api_url}/api/memory/forget/{id}");
            let client = reqwest::Client::new();
            let resp = client
                .delete(&url)
                .send()
                .await
                .map_err(|e| CliError::ApiCallFailed(format!("error: {e}")))?;
            let val: serde_json::Value = resp
                .json()
                .await
                .map_err(|e| CliError::ApiCallFailed(format!("error: {e}")))?;
            println!("{val}");
            Ok(())
        }
        MemoryCommands::Share { id, to, api_url } => {
            let body = serde_json::json!({"memory_id": id, "target_agent_ids": to});
            let url = format!("{api_url}/api/memory/share");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        MemoryCommands::Attest {
            id,
            agent,
            confidence,
            api_url,
        } => {
            let body = serde_json::json!({
                "memory_id": id,
                "attesting_agent_id": agent,
                "confidence": confidence
            });
            let url = format!("{api_url}/api/memory/attest");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        MemoryCommands::Export { dir, api_url } => {
            let body = serde_json::json!({"dir": dir});
            let url = format!("{api_url}/api/memory/export");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
        MemoryCommands::Reindex { dir, api_url } => {
            let body = serde_json::json!({"dir": dir});
            let url = format!("{api_url}/api/memory/reindex");
            crate::cli_http::post_and_print(&url, &body, false).await
        }
    }
}
