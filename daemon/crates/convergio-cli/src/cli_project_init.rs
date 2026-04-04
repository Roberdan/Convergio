// Project init handler — scaffolds a new project locally, then registers
// with the daemon via POST /api/plan-db/create.

use crate::cli_error::CliError;
use std::path::Path;

/// Options for `cvg project init`.
pub struct InitOpts<'a> {
    pub name: &'a str,
    pub lang: &'a str,
    pub license: &'a str,
    pub visibility: &'a str,
    pub org_id: &'a str,
    pub template: Option<&'a str>,
    pub local: bool,
    pub api_url: &'a str,
}

/// Run the full project init flow:
/// 1. Validate name
/// 2. Create project directory with scaffold files
/// 3. Initialize git repo
/// 4. Register project with the daemon API
pub async fn handle_init(opts: &InitOpts<'_>) -> Result<(), CliError> {
    validate_name(opts.name)?;
    let root = Path::new(opts.name);
    if root.exists() {
        return Err(CliError::InvalidInput(format!(
            "directory '{}' already exists",
            opts.name
        )));
    }

    // 1. Create directory structure
    std::fs::create_dir_all(root.join(".github/workflows")).map_err(CliError::Io)?;
    std::fs::create_dir_all(root.join(".claude")).map_err(CliError::Io)?;

    // 2. Write scaffold files
    let templates = crate::cli_project_init_templates::Templates::new(opts.name, opts.lang);
    write_file(root, ".gitignore", &templates.gitignore())?;
    write_file(root, ".claude/CLAUDE.md", &templates.claude_md())?;
    write_file(root, ".github/workflows/ci.yml", &templates.ci_yml())?;
    write_lang_files(root, opts.lang)?;
    eprintln!("  created scaffold in {}/", opts.name);

    // 3. Initialize git repo
    run_cmd_in("git", &["init"], opts.name).await?;
    run_cmd_in("git", &["add", "."], opts.name).await?;
    run_cmd_in(
        "git",
        &[
            "commit",
            "-m",
            "feat: initial project scaffold by Convergio",
        ],
        opts.name,
    )
    .await?;
    eprintln!("  git repo initialized with first commit");

    // 4. Register with daemon
    register_project(opts).await?;

    eprintln!("project '{}' initialized successfully", opts.name);
    Ok(())
}

fn validate_name(name: &str) -> Result<(), CliError> {
    if name.is_empty() {
        return Err(CliError::InvalidInput(
            "project name cannot be empty".into(),
        ));
    }
    let valid = name
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_');
    if !valid {
        return Err(CliError::InvalidInput(
            "project name must be alphanumeric, hyphens, or underscores".into(),
        ));
    }
    Ok(())
}

fn write_file(root: &Path, rel: &str, content: &str) -> Result<(), CliError> {
    let full = root.join(rel);
    if let Some(parent) = full.parent() {
        std::fs::create_dir_all(parent).map_err(CliError::Io)?;
    }
    std::fs::write(&full, content).map_err(CliError::Io)?;
    Ok(())
}

fn write_lang_files(root: &Path, lang: &str) -> Result<(), CliError> {
    match lang {
        "rust" => {
            write_file(
                root,
                "src/main.rs",
                "fn main() {\n    println!(\"hello\");\n}\n",
            )?;
        }
        "typescript" => {
            write_file(root, "src/index.ts", "console.log('hello');\n")?;
            std::fs::create_dir_all(root.join("src")).map_err(CliError::Io)?;
        }
        "python" => {
            write_file(root, "src/__init__.py", "")?;
            write_file(root, "src/main.py", "def main():\n    print('hello')\n")?;
        }
        _ => {} // unknown lang — skip language-specific files
    }
    Ok(())
}

async fn register_project(opts: &InitOpts<'_>) -> Result<(), CliError> {
    let body = serde_json::json!({
        "name": opts.name,
        "description": format!("{} — scaffolded by Convergio", opts.name),
        "language": opts.lang,
        "license": opts.license,
        "visibility": opts.visibility,
        "org_id": opts.org_id,
    });
    let url = format!("{}/api/plan-db/create", opts.api_url);
    match crate::cli_http::post_and_return(&url, &body).await {
        Ok(_) => {
            eprintln!("  registered project with daemon");
            Ok(())
        }
        Err(_) => {
            eprintln!("  warning: could not register with daemon (is it running?)");
            Ok(())
        }
    }
}

async fn run_cmd_in(prog: &str, args: &[&str], dir: &str) -> Result<(), CliError> {
    let status = tokio::process::Command::new(prog)
        .args(args)
        .current_dir(dir)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("failed to run {prog}: {e}")))?;
    if !status.success() {
        return Err(CliError::ApiCallFailed(format!(
            "{prog} exited with {}",
            status.code().unwrap_or(-1)
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_names_accepted() {
        assert!(validate_name("my-project").is_ok());
        assert!(validate_name("cool_app").is_ok());
        assert!(validate_name("app123").is_ok());
    }

    #[test]
    fn invalid_names_rejected() {
        assert!(validate_name("").is_err());
        assert!(validate_name("has space").is_err());
        assert!(validate_name("path/traversal").is_err());
        assert!(validate_name("special!chars").is_err());
    }

    #[test]
    fn scaffold_creates_files() {
        let tmp = tempfile::tempdir().unwrap();
        let root = tmp.path().join("test-proj");
        std::fs::create_dir_all(root.join(".github/workflows")).unwrap();
        std::fs::create_dir_all(root.join(".claude")).unwrap();

        let tpl = crate::cli_project_init_templates::Templates::new("test-proj", "rust");
        write_file(&root, ".gitignore", &tpl.gitignore()).unwrap();
        write_file(&root, ".claude/CLAUDE.md", &tpl.claude_md()).unwrap();
        write_file(&root, ".github/workflows/ci.yml", &tpl.ci_yml()).unwrap();
        write_lang_files(&root, "rust").unwrap();

        assert!(root.join(".gitignore").exists());
        assert!(root.join(".claude/CLAUDE.md").exists());
        assert!(root.join(".github/workflows/ci.yml").exists());
        assert!(root.join("src/main.rs").exists());
    }

    #[test]
    fn gitignore_matches_language() {
        let rust_tpl = crate::cli_project_init_templates::Templates::new("p", "rust");
        assert!(rust_tpl.gitignore().contains("target/"));

        let ts_tpl = crate::cli_project_init_templates::Templates::new("p", "typescript");
        assert!(ts_tpl.gitignore().contains("node_modules/"));

        let py_tpl = crate::cli_project_init_templates::Templates::new("p", "python");
        assert!(py_tpl.gitignore().contains("__pycache__/"));
    }
}
