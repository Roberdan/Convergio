//! convergio-build — Self-build: the daemon builds, tests, and deploys itself.
//!
//! Provides endpoints to trigger cargo check/test/build, track build history,
//! and deploy new binaries with automatic launchd restart.

pub mod builder;
pub mod deployer;
pub mod ext;
pub mod routes;
pub mod schema;
pub mod types;

pub use ext::BuildExtension;
pub use types::{BuildError, BuildResult};
