//! Tracing subscriber setup with file rotation and panic hooks.
//!
//! Adapted from ConvergioPlatform daemon_logging.rs.
//! Returns a WorkerGuard that must be held alive for the daemon's lifetime.

use convergio_types::platform_paths::convergio_data_dir;
use std::path::PathBuf;
use tracing_appender::non_blocking::WorkerGuard;
use tracing_subscriber::{fmt, prelude::*, EnvFilter};

/// Log directory: <data_dir>/logs/
fn log_dir() -> PathBuf {
    convergio_data_dir().join("logs")
}

/// Initialize daemon logging: file + stderr, panic hook.
/// Hold the returned guard alive for the daemon's lifetime.
pub fn init() -> WorkerGuard {
    init_inner(true)
}

/// File-only logging (no stderr).
pub fn init_file_only() -> WorkerGuard {
    init_inner(false)
}

fn init_inner(with_stderr: bool) -> WorkerGuard {
    let dir = log_dir();
    if let Err(e) = std::fs::create_dir_all(&dir) {
        eprintln!("telemetry: cannot create log dir {}: {e}", dir.display());
    }

    let file_appender = tracing_appender::rolling::daily(&dir, "daemon.log");
    let (non_blocking, guard) = tracing_appender::non_blocking(file_appender);

    let env_filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new("info,tower_http=warn"));

    let file_layer = fmt::layer()
        .with_writer(non_blocking)
        .with_ansi(false)
        .with_target(true)
        .with_thread_ids(true);

    if with_stderr {
        let stderr_layer = fmt::layer()
            .with_writer(std::io::stderr)
            .with_ansi(true)
            .with_target(false);
        tracing_subscriber::registry()
            .with(env_filter)
            .with(file_layer)
            .with(stderr_layer)
            .init();
    } else {
        tracing_subscriber::registry()
            .with(env_filter)
            .with(file_layer)
            .init();
    }

    install_panic_hook(&dir);
    guard
}

/// Panic hook writes crash info to daemon-crash.log before aborting.
fn install_panic_hook(log_dir: &std::path::Path) {
    let crash_path = log_dir.join("daemon-crash.log");
    std::panic::set_hook(Box::new(move |info| {
        let payload = if let Some(s) = info.payload().downcast_ref::<&str>() {
            s.to_string()
        } else if let Some(s) = info.payload().downcast_ref::<String>() {
            s.clone()
        } else {
            "unknown panic".to_string()
        };
        let location = info
            .location()
            .map(|l| format!("{}:{}:{}", l.file(), l.line(), l.column()))
            .unwrap_or_else(|| "unknown".to_string());

        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        let msg = format!(
            "[{ts}] PANIC pid={} at {location}: {payload}\n",
            std::process::id()
        );

        eprintln!("{msg}");
        let _ = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&crash_path)
            .and_then(|mut f| std::io::Write::write_all(&mut f, msg.as_bytes()));
    }));
}
