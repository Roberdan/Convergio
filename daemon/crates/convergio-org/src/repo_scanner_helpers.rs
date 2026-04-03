//! Internal helpers for repo scanning — file collection, language/framework detection.

use std::collections::HashMap;
use std::fs;
use std::path::Path;

use super::repo_scanner::CiInfo;

const SKIP_DIRS: &[&str] = &[
    ".git",
    "node_modules",
    "target",
    "__pycache__",
    ".next",
    "dist",
    "build",
];
const MAX_FILES_FOR_LINES: usize = 1000;

fn ext_to_lang(ext: &str) -> Option<&'static str> {
    match ext {
        "rs" => Some("Rust"),
        "ts" | "tsx" => Some("TypeScript"),
        "js" | "jsx" => Some("JavaScript"),
        "py" => Some("Python"),
        "swift" => Some("Swift"),
        "go" => Some("Go"),
        "java" => Some("Java"),
        "css" => Some("CSS"),
        "html" => Some("HTML"),
        _ => None,
    }
}

pub(crate) fn collect_files(root: &Path) -> Vec<std::path::PathBuf> {
    let mut files = Vec::new();
    let mut stack = vec![root.to_path_buf()];
    while let Some(dir) = stack.pop() {
        let entries = match fs::read_dir(&dir) {
            Ok(e) => e,
            Err(_) => continue,
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                if path.is_dir() {
                    if !SKIP_DIRS.contains(&name) {
                        stack.push(path);
                    }
                } else {
                    files.push(path);
                }
            }
        }
    }
    files
}

pub(crate) fn count_languages(files: &[std::path::PathBuf]) -> Vec<(String, usize)> {
    let mut counts: HashMap<&str, usize> = HashMap::new();
    for f in files {
        if let Some(ext) = f.extension().and_then(|e| e.to_str()) {
            if let Some(lang) = ext_to_lang(ext) {
                *counts.entry(lang).or_insert(0) += 1;
            }
        }
    }
    let mut langs: Vec<(String, usize)> = counts
        .into_iter()
        .map(|(k, v)| (k.to_string(), v))
        .collect();
    langs.sort_by(|a, b| b.1.cmp(&a.1));
    langs
}

pub(crate) fn detect_frameworks(root: &Path) -> Vec<String> {
    let mut fw = Vec::new();
    detect_js_frameworks(root, &mut fw);
    detect_rust_frameworks(root, &mut fw);
    detect_python_frameworks(root, &mut fw);
    if root.join("Package.swift").exists() {
        fw.push("Swift/iOS".to_string());
    }
    if root.join("Tauri.toml").exists() || root.join("src-tauri").exists() {
        fw.push("Tauri".to_string());
    }
    fw
}

fn detect_js_frameworks(root: &Path, fw: &mut Vec<String>) {
    let pkg = root.join("package.json");
    if let Ok(content) = fs::read_to_string(&pkg) {
        if content.contains("\"next\"") {
            fw.push("Next.js".to_string());
        }
        if content.contains("\"react\"") && !fw.contains(&"Next.js".to_string()) {
            fw.push("React".to_string());
        }
        if content.contains("\"vue\"") {
            fw.push("Vue".to_string());
        }
    }
}

fn detect_rust_frameworks(root: &Path, fw: &mut Vec<String>) {
    for cargo_path in &[root.join("Cargo.toml"), root.join("daemon/Cargo.toml")] {
        if let Ok(content) = fs::read_to_string(cargo_path) {
            if content.contains("axum") && !fw.contains(&"Axum".to_string()) {
                fw.push("Axum".to_string());
            }
            if content.contains("actix") && !fw.contains(&"Actix".to_string()) {
                fw.push("Actix".to_string());
            }
        }
    }
}

fn detect_python_frameworks(root: &Path, fw: &mut Vec<String>) {
    let reqs = root.join("requirements.txt");
    if let Ok(content) = fs::read_to_string(&reqs) {
        if content.contains("django") {
            fw.push("Django".to_string());
        }
        if content.contains("flask") {
            fw.push("Flask".to_string());
        }
        if content.contains("fastapi") {
            fw.push("FastAPI".to_string());
        }
    }
}

pub(crate) fn read_readme(root: &Path) -> String {
    for name in &["README.md", "README"] {
        if let Ok(content) = fs::read_to_string(root.join(name)) {
            let end = content
                .char_indices()
                .nth(500)
                .map(|(i, _)| i)
                .unwrap_or(content.len());
            return content[..end].to_string();
        }
    }
    String::new()
}

pub(crate) fn detect_ci(root: &Path) -> Option<CiInfo> {
    let wf_dir = root.join(".github/workflows");
    if wf_dir.is_dir() {
        let workflows: Vec<String> = fs::read_dir(&wf_dir)
            .ok()?
            .flatten()
            .filter_map(|e| {
                let p = e.path();
                let ext = p.extension().and_then(|x| x.to_str());
                if ext == Some("yml") || ext == Some("yaml") {
                    p.file_name().and_then(|n| n.to_str()).map(String::from)
                } else {
                    None
                }
            })
            .collect();
        if !workflows.is_empty() {
            return Some(CiInfo {
                provider: "github-actions".to_string(),
                workflows,
            });
        }
    }
    if root.join(".gitlab-ci.yml").exists() {
        return Some(CiInfo {
            provider: "gitlab-ci".to_string(),
            workflows: vec![".gitlab-ci.yml".to_string()],
        });
    }
    None
}

pub(crate) fn parse_dependencies(root: &Path) -> Vec<String> {
    let mut deps = Vec::new();
    parse_cargo_deps(root, &mut deps);
    parse_npm_deps(root, &mut deps);
    deps.truncate(20);
    deps
}

fn parse_cargo_deps(root: &Path, deps: &mut Vec<String>) {
    for cargo_path in &[root.join("Cargo.toml"), root.join("daemon/Cargo.toml")] {
        if let Ok(content) = fs::read_to_string(cargo_path) {
            let mut in_deps = false;
            for line in content.lines() {
                let trimmed = line.trim();
                if trimmed == "[dependencies]" {
                    in_deps = true;
                    continue;
                }
                if trimmed.starts_with('[') {
                    in_deps = false;
                    continue;
                }
                if in_deps {
                    if let Some(name) = trimmed.split('=').next() {
                        let name = name.trim();
                        if !name.is_empty() && !deps.contains(&name.to_string()) {
                            deps.push(name.to_string());
                        }
                    }
                }
            }
        }
    }
}

fn parse_npm_deps(root: &Path, deps: &mut Vec<String>) {
    let pkg = root.join("package.json");
    if let Ok(content) = fs::read_to_string(&pkg) {
        let mut in_deps = false;
        for line in content.lines() {
            let trimmed = line.trim();
            if trimmed.contains("\"dependencies\"") || trimmed.contains("\"devDependencies\"") {
                in_deps = true;
                continue;
            }
            if in_deps && trimmed.starts_with('}') {
                in_deps = false;
                continue;
            }
            if in_deps {
                if let Some(key) = trimmed.strip_prefix('"') {
                    if let Some(name) = key.split('"').next() {
                        if !deps.contains(&name.to_string()) {
                            deps.push(name.to_string());
                        }
                    }
                }
            }
        }
    }
}

pub(crate) fn count_total_lines(files: &[std::path::PathBuf]) -> usize {
    let limit = files.len().min(MAX_FILES_FOR_LINES);
    files[..limit]
        .iter()
        .filter_map(|f| fs::read_to_string(f).ok())
        .map(|c| c.lines().count())
        .sum()
}
