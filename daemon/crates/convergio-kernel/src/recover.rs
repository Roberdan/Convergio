//! Deterministic recovery chain — no LLM, purely rule-based.
//!
//! Critical: checkpoint → restart → reap → notify.
//! Warn (≥3 cycles): log + notify.

use super::types::KernelSeverity;

/// Recovery action to execute.
#[derive(Debug, Clone, PartialEq)]
pub enum RecoveryAction {
    None,
    Log {
        message: String,
    },
    Notify {
        channel: NotifyChannel,
        message: String,
    },
    Checkpoint,
    RestartPeer {
        hostname: String,
    },
    Reap {
        agent_id: String,
    },
}

/// Notification channel for recovery alerts.
#[derive(Debug, Clone, PartialEq)]
pub enum NotifyChannel {
    Ntfy,
    Local,
    Telegram,
}

/// Determine recovery actions based on severity and consecutive warn count.
pub fn plan_recovery(
    severity: KernelSeverity,
    consecutive_warns: u32,
    source: &str,
) -> Vec<RecoveryAction> {
    match severity {
        KernelSeverity::Ok => vec![RecoveryAction::None],
        KernelSeverity::Warn => {
            if consecutive_warns >= 3 {
                vec![
                    RecoveryAction::Log {
                        message: format!("warn cycle {consecutive_warns} for {source}"),
                    },
                    RecoveryAction::Notify {
                        channel: NotifyChannel::Local,
                        message: format!(
                            "persistent warning: {source} ({consecutive_warns} cycles)"
                        ),
                    },
                ]
            } else {
                vec![RecoveryAction::Log {
                    message: format!("warn cycle {consecutive_warns} for {source}"),
                }]
            }
        }
        KernelSeverity::Critical => {
            vec![
                RecoveryAction::Checkpoint,
                RecoveryAction::Notify {
                    channel: NotifyChannel::Telegram,
                    message: format!("CRITICAL: {source} — initiating recovery"),
                },
            ]
        }
    }
}
