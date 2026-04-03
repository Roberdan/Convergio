//! convergio-longrunning — Long-running execution protocol.
//!
//! Provides heartbeat monitoring, checkpoint persistence, budget guards,
//! progress streaming via SSE, and delegation chain tracking.
//!
//! Deps: types, db, ipc (SSE), orchestrator (via types only).

pub mod budget;
pub mod checkpoint;
pub mod delegation;
pub mod ext;
pub mod heartbeat;
pub mod progress;
pub mod reaper;
pub mod schema;
pub mod traits;
pub mod types;

pub use ext::LongRunningExtension;
pub use traits::LongRunnable;
pub use types::{LongRunError, LongRunResult};
