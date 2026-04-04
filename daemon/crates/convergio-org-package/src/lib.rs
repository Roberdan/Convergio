//! convergio-org-package — Org-as-package ecosystem.
//!
//! Install, sandbox, sign, and delegate between org packages.
//! Each org is isolated with DB prefix, route prefix, IPC channel
//! prefix, and budget hardcap enforcement.

pub mod delegation;
pub mod ext;
pub mod installer;
pub mod manifest;
pub mod routes;
pub mod sandbox;
pub mod signing;
pub mod token;

pub use delegation::{
    create_delegation, validate_delegation, DelegationError, DelegationRequest, DelegationResult,
    DelegationStatus,
};
pub use ext::OrgPackageExtension;
pub use installer::{
    check_not_installed, github_manifest_url, install_from_local, InstallError, InstallResult,
    PackageSource,
};
pub use manifest::{parse_manifest, ManifestError, OrgManifest};
pub use sandbox::{
    check_budget_limit, check_db_table, check_ipc_channel, check_route, create_sandbox, OrgSandbox,
    SandboxError,
};
pub use signing::{content_digest, sign_package, verify_signature, SigningError};
pub use token::{
    check_budget, check_ipc_publish, check_ipc_subscribe, create_org_claims, validate_expiry,
    OrgTokenBudget, OrgTokenClaims, OrgTokenPermissions, TokenError,
};
