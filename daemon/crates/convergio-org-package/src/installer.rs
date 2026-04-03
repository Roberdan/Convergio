//! Package installer — install orgs from local path, GitHub, or registry.
//!
//! Validates manifest, verifies signature, creates sandbox, and
//! records the installation in the database.

use crate::manifest::{parse_manifest, ManifestError, OrgManifest};
use crate::signing::{verify_signature, SigningError};

/// Source from which a package is installed.
#[derive(Debug, Clone)]
pub enum PackageSource {
    /// Local directory containing manifest.toml.
    Local(String),
    /// GitHub repo in "owner/repo" format.
    GitHub(String),
    /// Registry URL.
    Registry(String),
}

/// Installation result.
#[derive(Debug, Clone)]
pub struct InstallResult {
    pub org_name: String,
    pub version: String,
    pub source: String,
    pub sandbox_db_prefix: String,
    pub sandbox_route_prefix: String,
}

/// Installation errors.
#[derive(Debug, thiserror::Error)]
pub enum InstallError {
    #[error("manifest error: {0}")]
    Manifest(#[from] ManifestError),
    #[error("signature verification failed: {0}")]
    Signature(#[from] SigningError),
    #[error("IO error: {0}")]
    Io(String),
    #[error("already installed: {0} v{1}")]
    AlreadyInstalled(String, String),
    #[error("source not supported: {0}")]
    UnsupportedSource(String),
}

/// Install a package from a local directory.
///
/// Reads manifest.toml, validates it, verifies the optional signature,
/// and returns the install result. DB registration is handled by the
/// caller (ext.rs) since it needs the connection pool.
pub fn install_from_local(
    dir_path: &str,
    manifest_content: &str,
    signature: Option<&str>,
    signing_secret: Option<&[u8]>,
) -> Result<(OrgManifest, InstallResult), InstallError> {
    // Parse and validate manifest.
    let manifest = parse_manifest(manifest_content)?;

    // Verify signature if both signature and secret are provided.
    if let (Some(sig), Some(secret)) = (signature, signing_secret) {
        verify_signature(manifest_content.as_bytes(), sig, secret)?;
    }

    let sandbox = crate::sandbox::create_sandbox(&manifest);
    let result = InstallResult {
        org_name: manifest.package.name.clone(),
        version: manifest.package.version.clone(),
        source: format!("local:{dir_path}"),
        sandbox_db_prefix: sandbox.db_prefix,
        sandbox_route_prefix: sandbox.route_prefix,
    };

    Ok((manifest, result))
}

/// Install from a GitHub repo (downloads manifest.toml from main branch).
///
/// Returns the manifest content URL; actual download is done by the
/// caller with reqwest to keep this module sync-friendly.
pub fn github_manifest_url(repo: &str) -> Result<String, InstallError> {
    if !repo.contains('/') || repo.split('/').count() != 2 {
        return Err(InstallError::UnsupportedSource(format!(
            "invalid GitHub repo format: '{repo}' (expected 'owner/repo')"
        )));
    }
    Ok(format!(
        "https://raw.githubusercontent.com/{repo}/main/manifest.toml"
    ))
}

/// Validate that a package is not already installed (by name+version).
pub fn check_not_installed(
    installed: &[(String, String)],
    name: &str,
    version: &str,
) -> Result<(), InstallError> {
    if installed.iter().any(|(n, v)| n == name && v == version) {
        return Err(InstallError::AlreadyInstalled(name.into(), version.into()));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    const VALID_MANIFEST: &str = r#"
[package]
name = "acme-legal"
version = "1.0.0"
description = "ACME Legal Department"
author = "ACME Corp"
"#;

    #[test]
    fn install_local_valid_package() {
        let (manifest, result) =
            install_from_local("/tmp/acme-legal", VALID_MANIFEST, None, None).unwrap();
        assert_eq!(manifest.package.name, "acme-legal");
        assert_eq!(result.org_name, "acme-legal");
        assert_eq!(result.sandbox_db_prefix, "org_acme_legal_");
        assert_eq!(result.sandbox_route_prefix, "/org/acme-legal");
    }

    #[test]
    fn install_with_valid_signature() {
        let secret = b"test-secret-for-signing-packages";
        let sig = crate::signing::sign_package(VALID_MANIFEST.as_bytes(), secret).unwrap();
        let (_, result) =
            install_from_local("/tmp/acme-legal", VALID_MANIFEST, Some(&sig), Some(secret))
                .unwrap();
        assert_eq!(result.org_name, "acme-legal");
    }

    #[test]
    fn install_with_bad_signature_rejected() {
        let secret = b"test-secret-for-signing-packages";
        let err = install_from_local(
            "/tmp/acme-legal",
            VALID_MANIFEST,
            Some("bad-signature"),
            Some(secret),
        )
        .unwrap_err();
        assert!(err.to_string().contains("signature"));
    }

    #[test]
    fn github_url_valid() {
        let url = github_manifest_url("acme/legal-org").unwrap();
        assert!(url.contains("raw.githubusercontent.com"));
        assert!(url.contains("acme/legal-org"));
    }

    #[test]
    fn github_url_invalid_format() {
        let err = github_manifest_url("bad-format").unwrap_err();
        assert!(err.to_string().contains("invalid GitHub repo"));
    }

    #[test]
    fn already_installed_rejected() {
        let installed = vec![("acme-legal".into(), "1.0.0".into())];
        let err = check_not_installed(&installed, "acme-legal", "1.0.0").unwrap_err();
        assert!(err.to_string().contains("already installed"));
    }

    #[test]
    fn different_version_allowed() {
        let installed = vec![("acme-legal".into(), "1.0.0".into())];
        check_not_installed(&installed, "acme-legal", "2.0.0").unwrap();
    }
}
