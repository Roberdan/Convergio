// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Skill lint+transpile subcommands — replaces skill-lint.sh and skill-transpile-*.sh.
use crate::cli_error::CliError;
use clap::Subcommand;
use std::path::PathBuf;

// Re-export validation helpers so transpile module and tests keep working
pub(crate) use crate::cli_skill_validate::{capitalise, strip_h1, yaml_get};

// Re-export lint_one so cli_skill_tests.rs (super::*) keeps working
pub(crate) use crate::cli_skill_validators::lint_one;

pub(crate) const MIN_CONSTITUTION_VERSION: &str = "2.0.0";
pub(crate) const TOKEN_BUDGET_BYTES: u64 = 6144;

#[derive(Debug, Subcommand)]
pub enum SkillCommands {
    /// Validate a skill directory (skill.yaml + SKILL.md)
    Lint {
        /// Path to the skill directory (must contain skill.yaml and SKILL.md)
        skill_dir: PathBuf,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
        /// Lint all subdirectories inside this directory
        #[arg(long)]
        all: bool,
    },
    /// Transpile skill to provider format
    Transpile {
        /// Path to the skill directory
        skill_dir: PathBuf,
        /// Output directory (default: current directory)
        #[arg(long, default_value = ".")]
        output_dir: PathBuf,
        /// Target provider: claude-code, copilot-cli, generic-llm
        #[arg(long, default_value = "claude-code")]
        provider: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
    },
    /// Enable a skill and auto-activate its required agents/plugins
    Enable {
        /// Path to the skill directory
        skill_dir: PathBuf,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
    },
    /// Disable a skill and remove unshared plugins/agents
    Disable {
        /// Path to the skill directory
        skill_dir: PathBuf,
        /// Daemon API base URL
        #[arg(long, default_value = "http://localhost:8420")]
        api_url: String,
        /// Human-readable output instead of JSON
        #[arg(long)]
        human: bool,
    },
}

pub async fn handle(cmd: SkillCommands) -> Result<(), CliError> {
    match cmd {
        SkillCommands::Lint {
            skill_dir,
            human,
            all,
        } => {
            handle_lint(&skill_dir, human, all)?;
        }
        SkillCommands::Transpile {
            skill_dir,
            output_dir,
            provider,
            human,
        } => {
            crate::cli_skill_transpile::handle_transpile(
                &skill_dir,
                &output_dir,
                &provider,
                human,
            )?;
        }
        SkillCommands::Enable {
            skill_dir,
            api_url,
            human,
        } => {
            crate::cli_skill_enable::handle(&skill_dir, &api_url, human).await?;
        }
        SkillCommands::Disable {
            skill_dir,
            api_url,
            human,
        } => {
            crate::cli_skill_disable::handle(&skill_dir, &api_url, human).await?;
        }
    }
    Ok(())
}

// -- Lint --------------------------------------------------------------------

fn handle_lint(skill_dir: &PathBuf, human: bool, all: bool) -> Result<(), CliError> {
    if all {
        let entries = std::fs::read_dir(skill_dir).map_err(|err| {
            CliError::InvalidInput(format!(
                "error reading directory {}: {err}",
                skill_dir.display()
            ))
        })?;
        let mut results = Vec::new();
        for entry in entries.flatten() {
            if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                results.push(lint_one(&entry.path()));
            }
        }
        if results.is_empty() {
            return Err(CliError::NotFound(format!(
                "no skill directories found in {}",
                skill_dir.display()
            )));
        }
        let pass = results.iter().filter(|r| r.ok).count();
        let fail = results.iter().filter(|r| !r.ok).count();
        if human {
            for r in &results {
                for msg in &r.messages {
                    println!("{msg}");
                }
            }
            println!("\nSummary: {pass} passed, {fail} failed");
        } else {
            println!(
                "{}",
                serde_json::json!({
                    "results": results.iter().map(|r| r.to_json()).collect::<Vec<_>>(),
                    "summary": {"pass": pass, "fail": fail}
                })
            );
        }
        if fail > 0 {
            return Err(CliError::NotFound(format!("{fail} skill(s) failed lint")));
        }
    } else {
        let result = lint_one(skill_dir);
        let pass: usize = if result.ok { 1 } else { 0 };
        let fail = 1 - pass;
        if human {
            for msg in &result.messages {
                println!("{msg}");
            }
            println!("\nSummary: {pass} passed, {fail} failed");
        } else {
            println!(
                "{}",
                serde_json::json!({
                    "results": [result.to_json()],
                    "summary": {"pass": pass, "fail": fail}
                })
            );
        }
        if !result.ok {
            return Err(CliError::NotFound("skill failed lint".into()));
        }
    }
    Ok(())
}

pub(crate) struct LintResult {
    pub(crate) skill: String,
    pub(crate) ok: bool,
    pub(crate) messages: Vec<String>,
}
impl LintResult {
    pub(crate) fn to_json(&self) -> serde_json::Value {
        serde_json::json!({"skill": self.skill, "ok": self.ok, "messages": self.messages})
    }
}

#[cfg(test)]
#[path = "cli_skill_tests.rs"]
mod tests;
