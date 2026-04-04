//! Tests for convergio-kernel.

mod ext_tests {
    use convergio_types::extension::Extension;
    use convergio_types::manifest::ModuleKind;

    use crate::ext::KernelExtension;

    #[test]
    fn manifest_is_extension_kind() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let ext = KernelExtension::new(pool);
        let m = ext.manifest();
        assert_eq!(m.id, "convergio-kernel");
        assert!(matches!(m.kind, ModuleKind::Extension));
        assert!(!m.provides.is_empty());
        assert!(m.provides.iter().any(|c| c.name == "local-inference"));
        assert!(m.provides.iter().any(|c| c.name == "evidence-gate"));
    }

    #[test]
    fn has_four_migrations() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let ext = KernelExtension::new(pool);
        let migs = ext.migrations();
        assert_eq!(migs.len(), 4);
        assert_eq!(migs[0].description, "kernel_events table");
        assert_eq!(migs[1].description, "kernel_verifications table");
        assert_eq!(migs[2].description, "kernel_config table");
        assert_eq!(migs[3].description, "knowledge_base table");
    }

    #[test]
    fn migrations_sql_is_valid() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        let ext = KernelExtension::new(pool.clone());
        for mig in ext.migrations() {
            conn.execute_batch(mig.up).unwrap_or_else(|e| {
                panic!("migration {} failed: {e}", mig.description);
            });
        }
    }

    #[test]
    fn has_scheduled_tasks() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let ext = KernelExtension::new(pool);
        let tasks = ext.scheduled_tasks();
        assert_eq!(tasks.len(), 2);
        assert!(tasks.iter().any(|t| t.name == "kernel-monitor"));
    }
}

mod engine_tests {
    use crate::engine::KernelEngine;
    use crate::types::{InferenceLevel, KernelConfig, KernelSeverity};

    #[test]
    fn classify_critical_daemon_down() {
        let engine = KernelEngine::default();
        let action = engine.classify("daemon is down, cannot reach health endpoint");
        assert_eq!(action.severity, KernelSeverity::Critical);
        assert_eq!(action.action, "restart");
    }

    #[test]
    fn classify_warn_stalled() {
        let engine = KernelEngine::default();
        let action = engine.classify("agent is stalled for 5 minutes");
        assert_eq!(action.severity, KernelSeverity::Warn);
        assert_eq!(action.action, "throttle");
    }

    #[test]
    fn classify_ok_normal() {
        let engine = KernelEngine::default();
        let action = engine.classify("everything looks good");
        assert_eq!(action.severity, KernelSeverity::Ok);
        assert_eq!(action.action, "none");
    }

    #[test]
    fn route_inference_local_for_short() {
        let engine = KernelEngine::default();
        assert_eq!(
            engine.route_inference("what is the status?"),
            InferenceLevel::Local
        );
    }

    #[test]
    fn route_inference_cloud_for_code() {
        let engine = KernelEngine::default();
        let query = "Please review this code:\n```rust\nfn main() {}\n```";
        assert_eq!(engine.route_inference(query), InferenceLevel::Cloud);
    }

    #[test]
    fn status_reports_uptime() {
        let engine = KernelEngine::default();
        let status = engine.status();
        assert!(!status.models_loaded);
        assert!(status.uptime_secs < 5);
    }

    #[test]
    fn record_check_updates_timestamp() {
        let mut engine = KernelEngine::new(KernelConfig::default());
        assert!(engine.status().last_check.is_none());
        engine.record_check();
        assert!(engine.status().last_check.is_some());
    }
}

mod verify_tests {
    use crate::types::KernelSeverity;
    use crate::verify::verify_task;

    #[test]
    fn verify_passes_when_no_outputs() {
        let report = verify_task(1, "done", None, &[]);
        assert!(report.passed);
        assert_eq!(report.severity, KernelSeverity::Ok);
    }

    #[test]
    fn verify_fails_when_output_missing() {
        let report = verify_task(1, "done", None, &["/nonexistent/file.txt".to_string()]);
        assert!(!report.passed);
        assert_eq!(report.severity, KernelSeverity::Warn);
        assert!(report.reason.contains("output_exists"));
    }
}

mod recover_tests {
    use crate::recover::*;
    use crate::types::KernelSeverity;

    #[test]
    fn ok_severity_no_action() {
        let actions = plan_recovery(KernelSeverity::Ok, 0, "test");
        assert_eq!(actions, vec![RecoveryAction::None]);
    }

    #[test]
    fn warn_under_threshold_logs_only() {
        let actions = plan_recovery(KernelSeverity::Warn, 1, "test");
        assert_eq!(actions.len(), 1);
        assert!(matches!(actions[0], RecoveryAction::Log { .. }));
    }

    #[test]
    fn warn_over_threshold_notifies() {
        let actions = plan_recovery(KernelSeverity::Warn, 3, "test");
        assert_eq!(actions.len(), 2);
        assert!(matches!(actions[1], RecoveryAction::Notify { .. }));
    }

    #[test]
    fn critical_checkpoints_and_notifies() {
        let actions = plan_recovery(KernelSeverity::Critical, 0, "daemon down");
        assert!(actions
            .iter()
            .any(|a| matches!(a, RecoveryAction::Checkpoint)));
        assert!(actions.iter().any(|a| matches!(
            a,
            RecoveryAction::Notify {
                channel: NotifyChannel::Telegram,
                ..
            }
        )));
    }
}

mod monitor_tests {
    use crate::monitor::*;
    use crate::types::KernelSeverity;

    #[test]
    fn classify_all_ok() {
        let results = vec![crate::types::KernelCheckResult {
            check_name: "test".to_string(),
            ok: true,
            details: "fine".to_string(),
        }];
        assert_eq!(classify_results(&results), KernelSeverity::Ok);
    }

    #[test]
    fn classify_critical_on_daemon_health() {
        let results = vec![crate::types::KernelCheckResult {
            check_name: "daemon_health".to_string(),
            ok: false,
            details: "down".to_string(),
        }];
        assert_eq!(classify_results(&results), KernelSeverity::Critical);
    }

    #[test]
    fn classify_warn_on_non_critical_failure() {
        let results = vec![crate::types::KernelCheckResult {
            check_name: "disk_space".to_string(),
            ok: false,
            details: "low".to_string(),
        }];
        assert_eq!(classify_results(&results), KernelSeverity::Warn);
    }
}

mod types_tests {
    use crate::types::*;

    #[test]
    fn severity_display() {
        assert_eq!(KernelSeverity::Ok.to_string(), "ok");
        assert_eq!(KernelSeverity::Warn.to_string(), "warn");
        assert_eq!(KernelSeverity::Critical.to_string(), "critical");
    }

    #[test]
    fn kernel_config_default() {
        let cfg = KernelConfig::default();
        assert!(cfg.active_node.is_none());
        assert!(cfg.default_model.contains("qwen"));
    }
}
