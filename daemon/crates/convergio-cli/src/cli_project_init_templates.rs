// Template generators for `cvg project init` scaffold files.
// Each method returns a String with the file content for the given language.

/// Holds project metadata used to generate scaffold templates.
pub struct Templates<'a> {
    name: &'a str,
    lang: &'a str,
}

impl<'a> Templates<'a> {
    pub fn new(name: &'a str, lang: &'a str) -> Self {
        Self { name, lang }
    }

    /// Generate .gitignore content based on detected language.
    pub fn gitignore(&self) -> String {
        let common = ".env\n.DS_Store\n*.log\n";
        let lang_specific = match self.lang {
            "rust" => "target/\nCargo.lock\n",
            "typescript" => "node_modules/\ndist/\n*.tsbuildinfo\n",
            "python" => "__pycache__/\n*.pyc\n.venv/\ndist/\n*.egg-info/\n",
            _ => "target/\nCargo.lock\n", // default to Rust
        };
        format!("{common}{lang_specific}")
    }

    /// Generate CLAUDE.md template with convergio project rules.
    pub fn claude_md(&self) -> String {
        format!(
            r#"# {name} — CLAUDE.md

## What is this

{name} is a Convergio-managed project.

## Rules

- Code and docs in **English**.
- Max **250 lines per file**.
- Conventional commits.
- Every PR must pass CI before merge.

## Running

```bash
# Check the project compiles
cargo check
# Run tests
cargo test
```

## Testing

- Write tests first (RED-GREEN-REFACTOR).
- 80% coverage for business logic, 100% for critical paths.
- Mock external boundaries only (network, filesystem, time).

## Architecture

Describe your architecture here.
"#,
            name = self.name
        )
    }

    /// Generate CI workflow for GitHub Actions.
    pub fn ci_yml(&self) -> String {
        match self.lang {
            "typescript" => self.ci_yml_typescript(),
            "python" => self.ci_yml_python(),
            _ => self.ci_yml_rust(), // default to Rust
        }
    }

    fn ci_yml_rust(&self) -> String {
        format!(
            r#"name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy
      - name: cargo check
        run: cargo check --workspace
      - name: cargo test
        run: cargo test --workspace
      - name: cargo clippy
        run: cargo clippy --workspace -- -D warnings
"#
        )
    }

    fn ci_yml_typescript(&self) -> String {
        format!(
            r#"name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint
      - run: npm test
"#
        )
    }

    fn ci_yml_python(&self) -> String {
        format!(
            r#"name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest
"#
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn claude_md_contains_project_name() {
        let tpl = Templates::new("acme-app", "rust");
        let md = tpl.claude_md();
        assert!(md.contains("acme-app"));
        assert!(md.contains("250 lines"));
    }

    #[test]
    fn ci_yml_rust_has_clippy() {
        let tpl = Templates::new("proj", "rust");
        let ci = tpl.ci_yml();
        assert!(ci.contains("cargo clippy"));
        assert!(ci.contains("cargo test"));
    }

    #[test]
    fn ci_yml_typescript_has_npm() {
        let tpl = Templates::new("proj", "typescript");
        let ci = tpl.ci_yml();
        assert!(ci.contains("npm ci"));
        assert!(ci.contains("npm test"));
    }

    #[test]
    fn ci_yml_python_has_pytest() {
        let tpl = Templates::new("proj", "python");
        let ci = tpl.ci_yml();
        assert!(ci.contains("pytest"));
        assert!(ci.contains("ruff"));
    }

    #[test]
    fn unknown_lang_defaults_to_rust() {
        let tpl = Templates::new("proj", "go");
        let gi = tpl.gitignore();
        assert!(gi.contains("target/")); // defaults to Rust
        let ci = tpl.ci_yml();
        assert!(ci.contains("cargo check"));
    }
}
