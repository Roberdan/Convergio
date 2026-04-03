// Project init handler — scaffolds a new project via the daemon API,
// then creates the repo locally or on GitHub.

use crate::cli_error::CliError;

/// Run the full project init flow:
/// 1. Call POST /api/projects/scaffold to get file tree
/// 2. Create repo (gh repo create or git init)
/// 3. Write generated files
/// 4. Configure branch protection if GitHub
/// 5. First commit + push
pub async fn handle_init(
    name: &str,
    lang: &str,
    license: &str,
    visibility: &str,
    org_id: &str,
    template: Option<&str>,
    local: bool,
    api_url: &str,
) -> Result<(), CliError> {
    // 1. Scaffold via daemon API
    let mut body = serde_json::json!({
        "name": name,
        "description": format!("{name} — scaffolded by Convergio"),
        "language": lang,
        "license": license,
        "visibility": visibility,
        "org_id": org_id,
    });
    if let Some(tpl) = template {
        body["template"] = serde_json::Value::String(tpl.to_string());
    }
    let url = format!("{api_url}/api/projects/scaffold");
    let scaffold = crate::cli_http::post_and_return(&url, &body)
        .await
        .map_err(|_| CliError::ApiCallFailed("scaffold API call failed".into()))?;

    let files = scaffold["files"]
        .as_array()
        .ok_or_else(|| CliError::ApiCallFailed("invalid scaffold response".into()))?;

    // 2. Create repo
    if local {
        create_local_repo(name).await?;
    } else {
        create_github_repo(name, visibility).await?;
    }

    // 3. Write files
    write_scaffold_files(name, files)?;

    // 4. Branch protection (GitHub only)
    if !local {
        if let Some(bp) = scaffold.get("branch_protection") {
            configure_branch_protection(name, bp).await;
        }
    }

    // 5. First commit + push
    first_commit(name, local).await?;

    eprintln!("project {name} initialized successfully");
    Ok(())
}

async fn create_local_repo(name: &str) -> Result<(), CliError> {
    run_cmd("git", &["init", name]).await?;
    Ok(())
}

async fn create_github_repo(name: &str, visibility: &str) -> Result<(), CliError> {
    let vis_flag = format!("--{visibility}");
    run_cmd("gh", &["repo", "create", name, &vis_flag, "--clone"])
        .await?;
    Ok(())
}

fn write_scaffold_files(
    name: &str,
    files: &[serde_json::Value],
) -> Result<(), CliError> {
    for file in files {
        let path_str = file["path"].as_str().unwrap_or("");
        let content = file["content"].as_str().unwrap_or("");
        if path_str.is_empty() {
            continue;
        }
        let full = std::path::Path::new(name).join(path_str);
        if let Some(parent) = full.parent() {
            std::fs::create_dir_all(parent).map_err(CliError::Io)?;
        }
        std::fs::write(&full, content).map_err(CliError::Io)?;
    }
    Ok(())
}

async fn configure_branch_protection(
    name: &str,
    bp: &serde_json::Value,
) {
    let branch = bp["branch"].as_str().unwrap_or("main");
    let checks: Vec<String> = bp["required_checks"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .filter_map(|v| v.as_str().map(String::from))
                .collect()
        })
        .unwrap_or_default();

    let checks_json = serde_json::json!({
        "required_status_checks": {
            "strict": true,
            "contexts": checks,
        },
        "enforce_admins": false,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": true,
            "required_approving_review_count": 1,
        },
        "restrictions": null,
    });

    let endpoint = format!(
        "repos/{{owner}}/{name}/branches/{branch}/protection"
    );
    let body_str = checks_json.to_string();
    let _ = std::process::Command::new("gh")
        .args(["api", &endpoint, "-X", "PUT", "--input", "-"])
        .current_dir(name)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn()
        .and_then(|mut child| {
            use std::io::Write;
            if let Some(ref mut stdin) = child.stdin {
                let _ = stdin.write_all(body_str.as_bytes());
            }
            let _ = child.wait();
            Ok(())
        });
}

async fn first_commit(name: &str, local: bool) -> Result<(), CliError> {
    run_cmd_in("git", &["add", "."], name).await?;
    run_cmd_in(
        "git",
        &["commit", "-m", "feat: initial project scaffold by Convergio"],
        name,
    )
    .await?;
    if !local {
        run_cmd_in("git", &["push", "-u", "origin", "main"], name).await?;
    }
    Ok(())
}

async fn run_cmd(prog: &str, args: &[&str]) -> Result<(), CliError> {
    let status = tokio::process::Command::new(prog)
        .args(args)
        .status()
        .await
        .map_err(|e| {
            CliError::ApiCallFailed(format!("failed to run {prog}: {e}"))
        })?;
    if !status.success() {
        return Err(CliError::ApiCallFailed(format!(
            "{prog} exited with {}",
            status.code().unwrap_or(-1)
        )));
    }
    Ok(())
}

async fn run_cmd_in(
    prog: &str,
    args: &[&str],
    dir: &str,
) -> Result<(), CliError> {
    let status = tokio::process::Command::new(prog)
        .args(args)
        .current_dir(dir)
        .status()
        .await
        .map_err(|e| {
            CliError::ApiCallFailed(format!("failed to run {prog}: {e}"))
        })?;
    if !status.success() {
        return Err(CliError::ApiCallFailed(format!(
            "{prog} exited with {}",
            status.code().unwrap_or(-1)
        )));
    }
    Ok(())
}
