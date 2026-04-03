//! Repo analysis — scans a local repository and produces a structured profile.

use std::path::Path;

use super::repo_scanner_helpers::{
    collect_files, count_languages, count_total_lines, detect_ci, detect_frameworks,
    parse_dependencies, read_readme,
};

/// Profile of a scanned repository.
pub struct RepoProfile {
    pub path: String,
    pub languages: Vec<(String, usize)>,
    pub frameworks: Vec<String>,
    pub structure: RepoStructure,
    pub ci: Option<CiInfo>,
    pub readme_summary: String,
    pub total_files: usize,
    pub total_lines: usize,
    pub dependencies: Vec<String>,
}

/// High-level structural indicators found in the repo.
pub struct RepoStructure {
    pub has_src: bool,
    pub has_tests: bool,
    pub has_docs: bool,
    pub has_ci: bool,
    pub manifest_files: Vec<String>,
}

/// CI provider and workflow files detected.
pub struct CiInfo {
    pub provider: String,
    pub workflows: Vec<String>,
}

const MANIFEST_NAMES: &[&str] = &[
    "Cargo.toml", "package.json", "requirements.txt", "go.mod", "Package.swift",
];

/// Scan a repository at `path` and produce a RepoProfile.
pub fn scan_repo(path: &Path) -> Result<RepoProfile, String> {
    if !path.is_dir() {
        return Err(format!("path is not a directory: {}", path.display()));
    }

    let files = collect_files(path);
    let languages = count_languages(&files);
    let frameworks = detect_frameworks(path);
    let readme_summary = read_readme(path);
    let ci = detect_ci(path);
    let dependencies = parse_dependencies(path);
    let total_lines = count_total_lines(&files);

    let mut manifest_files: Vec<String> = Vec::new();
    for name in MANIFEST_NAMES {
        if path.join(name).exists() {
            manifest_files.push(name.to_string());
        }
    }
    if let Ok(entries) = std::fs::read_dir(path) {
        for entry in entries.flatten() {
            if entry.path().is_dir() {
                for name in MANIFEST_NAMES {
                    if entry.path().join(name).exists() {
                        let rel = format!("{}/{}", entry.file_name().to_string_lossy(), name);
                        if !manifest_files.contains(&rel) {
                            manifest_files.push(rel);
                        }
                    }
                }
            }
        }
    }

    let structure = RepoStructure {
        has_src: path.join("src").is_dir() || path.join("daemon/src").is_dir(),
        has_tests: path.join("tests").is_dir() || path.join("daemon/tests").is_dir(),
        has_docs: path.join("docs").is_dir(),
        has_ci: ci.is_some(),
        manifest_files,
    };

    Ok(RepoProfile {
        path: path.display().to_string(),
        languages,
        frameworks,
        structure,
        ci,
        readme_summary,
        total_files: files.len(),
        total_lines,
        dependencies,
    })
}
