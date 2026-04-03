// Template content for project scaffolding — one const per file per language.

/// CLAUDE.md template skeleton for scaffolded projects.
pub const CLAUDE_MD: &str = r#"# {name}

## What is this
{description}

## Rules
- Conventional commits
- Max 250 lines per file
- English code, Italian conversation
"#;

pub const LICENSE_MIT: &str = r#"MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"#;

pub const LICENSE_APACHE2: &str = "Apache License, Version 2.0\n\
    See https://www.apache.org/licenses/LICENSE-2.0\n";

pub const LICENSE_GPL3: &str = "GNU General Public License v3.0\n\
    See https://www.gnu.org/licenses/gpl-3.0.en.html\n";

pub const README_MD: &str = r#"# {name}

{description}

## Getting started

See CLAUDE.md for project conventions.
"#;

pub const CODEOWNERS: &str = "* @{owner}\n";

pub const GITIGNORE_RUST: &str = "/target\nCargo.lock\n*.swp\n.DS_Store\n";
pub const GITIGNORE_TS: &str = "node_modules/\ndist/\n*.swp\n.DS_Store\n";
pub const GITIGNORE_PYTHON: &str = "__pycache__/\n*.pyc\n.venv/\ndist/\n\
    *.egg-info/\n.DS_Store\n";

// --- Rust templates ---

pub const RUST_CARGO_TOML: &str = r#"[package]
name = "{name}"
version = "0.1.0"
edition = "2021"
description = "{description}"
license = "{license_spdx}"

[dependencies]
"#;

pub const RUST_MAIN_RS: &str = r#"fn main() {
    println!("Hello from {name}");
}
"#;

pub const RUST_CI_YML: &str = r#"name: CI
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy, rustfmt
      - run: cargo check --workspace
      - run: cargo test --workspace
      - run: cargo clippy --workspace -- -D warnings
      - run: cargo fmt --all -- --check
"#;

// --- TypeScript templates ---

pub const TS_PACKAGE_JSON: &str = r#"{{
  "name": "{name}",
  "version": "0.1.0",
  "description": "{description}",
  "license": "{license_spdx}",
  "scripts": {{
    "build": "tsc",
    "lint": "eslint src",
    "test": "vitest run"
  }},
  "devDependencies": {{
    "typescript": "^5.4",
    "eslint": "^9",
    "vitest": "^2"
  }}
}}
"#;

pub const TS_TSCONFIG: &str = r#"{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
"#;

pub const TS_INDEX: &str = "export function main(): void {\n  \
    console.log('Hello from {name}');\n}\n\nmain();\n";

pub const TS_CI_YML: &str = r#"name: CI
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npx eslint src
      - run: npx vitest run
"#;

// --- Python templates ---

pub const PY_PYPROJECT: &str = r#"[project]
name = "{name}"
version = "0.1.0"
description = "{description}"
license = "{license_spdx}"
requires-python = ">=3.11"

[tool.ruff]
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
"#;

pub const PY_INIT: &str = "\"\"\"Top-level package for {name}.\"\"\"\n";

pub const PY_CI_YML: &str = r#"name: CI
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff pytest
      - run: ruff check src
      - run: pytest
"#;
