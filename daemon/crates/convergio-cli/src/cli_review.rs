// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Review subcommand — register/check/reset plan reviews via daemon HTTP API.

use clap::Subcommand;

/// Valid verdict values for `cvg review register`.
const VALID_VERDICTS: &[&str] = &["proceed", "revise", "reject"];

/// Returns true if the verdict is one of the accepted values.
pub fn is_valid_verdict(verdict: &str) -> bool {
    VALID_VERDICTS.contains(&verdict)
}

#[derive(Debug, Subcommand)]
pub enum ReviewCommands {
    /// Register a plan review record.
    ///
    /// Usage (with plan ID):
    ///   cvg review register --plan-id <ID> <reviewer_agent> <verdict> [--suggestions ...]
    ///
    /// Usage (pre-plan, by spec file — use before cvg plan create):
    ///   cvg review register --spec-file <path> <reviewer_agent> <verdict> [--suggestions ...]
    ///
    /// Verdict must be one of: proceed | revise | reject
    Register {
        /// Plan DB ID (optional if --spec-file is supplied)
        #[arg(long)]
        plan_id: Option<i64>,
        /// Path to the spec file (optional if --plan-id is supplied).
        /// When supplied and plan_id is absent, the review is stored without a
        /// plan link and automatically linked when `cvg plan create` imports
        /// the matching spec file.
        #[arg(long)]
        spec_file: Option<String>,
        /// Reviewer agent name (e.g. plan-reviewer, plan-business-advisor)
        reviewer_agent: String,
        /// Verdict: must be one of proceed | revise | reject
        verdict: String,
        /// Optional suggestions text
        #[arg(long)]
        suggestions: Option<String>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Check review counts for a plan
    Check {
        /// Plan ID
        plan_id: i64,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
    /// Reset (delete) all reviews for a plan (omit plan_id to reset pre-plan state)
    Reset {
        /// Plan ID (optional — omit to reset without a plan, e.g. before cvg plan create)
        plan_id: Option<i64>,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
    },
}

pub async fn handle(cmd: ReviewCommands) {
    match cmd {
        ReviewCommands::Register {
            plan_id,
            spec_file,
            reviewer_agent,
            verdict,
            suggestions,
            human,
            api_url,
        } => {
            // Validate verdict before sending — catch user errors locally with clear message.
            if !is_valid_verdict(&verdict) {
                eprintln!(
                    "error: invalid verdict '{verdict}'\n\
                     Valid values: proceed | revise | reject\n\
                     Usage: cvg review register [--plan-id <ID> | --spec-file <path>] \
                     <reviewer_agent> <verdict>"
                );
                std::process::exit(1);
            }

            // At least one of plan_id or spec_file must be supplied.
            if plan_id.is_none() && spec_file.is_none() {
                eprintln!(
                    "error: supply either --plan-id <ID> or --spec-file <path>\n\
                     Usage: cvg review register [--plan-id <ID> | --spec-file <path>] \
                     <reviewer_agent> <verdict>"
                );
                std::process::exit(1);
            }

            let body = serde_json::json!({
                "plan_id": plan_id,
                "spec_file": spec_file,
                "reviewer_agent": reviewer_agent,
                "verdict": verdict,
                "suggestions": suggestions,
            });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/review/register"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        ReviewCommands::Check {
            plan_id,
            human,
            api_url,
        } => {
            if let Err(e) = crate::cli_http::fetch_and_print(
                &format!("{api_url}/api/plan-db/review/check?plan_id={plan_id}"),
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
        ReviewCommands::Reset {
            plan_id,
            human,
            api_url,
        } => {
            let body = serde_json::json!({ "plan_id": plan_id.unwrap_or(0) });
            if let Err(e) = crate::cli_http::post_and_print(
                &format!("{api_url}/api/plan-db/review/reset"),
                &body,
                human,
            )
            .await
            {
                eprintln!("error: {e}");
            }
        }
    }
}

#[cfg(test)]
#[path = "cli_review_tests.rs"]
mod tests;
