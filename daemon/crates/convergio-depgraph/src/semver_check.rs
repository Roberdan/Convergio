//! SemVer compatibility checking between provided and required versions.

use semver::{Version, VersionReq};

/// Error returned when a version does not satisfy a requirement.
#[derive(Debug)]
pub struct SemVerError {
    pub provided: String,
    pub required: String,
}

/// Check that `provided_version` satisfies `version_req_str`.
///
/// Both strings are parsed as semver; returns Ok(()) on match,
/// Err with details on mismatch or parse failure.
pub fn check(provided_version: &str, version_req_str: &str) -> Result<(), SemVerError> {
    let provided = Version::parse(provided_version).map_err(|_| SemVerError {
        provided: provided_version.to_string(),
        required: version_req_str.to_string(),
    })?;

    let req = VersionReq::parse(version_req_str).map_err(|_| SemVerError {
        provided: provided_version.to_string(),
        required: version_req_str.to_string(),
    })?;

    if req.matches(&provided) {
        Ok(())
    } else {
        Err(SemVerError {
            provided: provided_version.to_string(),
            required: version_req_str.to_string(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn exact_match() {
        assert!(check("1.0.0", "=1.0.0").is_ok());
    }

    #[test]
    fn range_match() {
        assert!(check("1.2.3", ">=1.0.0, <2.0.0").is_ok());
    }

    #[test]
    fn range_mismatch() {
        assert!(check("0.9.0", ">=1.0.0").is_err());
    }

    #[test]
    fn caret_match() {
        assert!(check("0.1.5", "^0.1.0").is_ok());
    }

    #[test]
    fn caret_mismatch() {
        assert!(check("0.2.0", "^0.1.0").is_err());
    }

    #[test]
    fn wildcard_match() {
        assert!(check("3.7.1", ">=0.1.0").is_ok());
    }

    #[test]
    fn invalid_version_errors() {
        assert!(check("not-a-version", ">=1.0.0").is_err());
    }

    #[test]
    fn invalid_req_errors() {
        assert!(check("1.0.0", "not-a-req!!!").is_err());
    }
}
