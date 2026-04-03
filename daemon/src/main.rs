//! Convergio daemon — collects extensions, starts the server.
//!
//! This binary wires all extensions together and launches the daemon.
//! Business logic lives in the crates; this is just the entry point.

use convergio_db::pool::{create_pool, ConnPool};
use convergio_server::{build_router, load_config, run_server, ServerState};
use convergio_telemetry::health::HealthRegistry;
use convergio_telemetry::metrics::MetricsCollector;
use convergio_types::extension::{AppContext, Extension};
use std::sync::{Arc, RwLock};
use tokio::sync::Notify;

fn register_extensions(
    pool: ConnPool,
) -> Vec<Arc<dyn Extension>> {
    let notify = Arc::new(Notify::new());

    vec![
        // Infrastructure
        Arc::new(convergio_ipc::IpcExtension::new(pool.clone())),
        Arc::new(convergio_mesh::ext::MeshExtension::new(pool.clone())),
        // Platform services
        Arc::new(convergio_orchestrator::OrchestratorExtension::new(
            pool.clone(),
            notify,
        )),
        Arc::new(convergio_inference::InferenceExtension::new(pool.clone())),
        Arc::new(convergio_prompts::ext::PromptsExtension::new(pool.clone())),
        Arc::new(convergio_agent_runtime::AgentRuntimeExtension::new(
            pool.clone(),
        )),
        // Extensions
        Arc::new(convergio_kernel::KernelExtension),
        Arc::new(convergio_org::OrgExtension),
        Arc::new(convergio_voice::VoiceExtension),
        // Ecosystem
        Arc::new(convergio_org_package::OrgPackageExtension),
        Arc::new(convergio_http_bridge::HttpBridgeExtension::new()),
        // Platform tools
        Arc::new(convergio_longrunning::LongRunningExtension::new(
            pool.clone(),
        )),
        Arc::new(convergio_billing::BillingExtension::new(pool.clone())),
        Arc::new(convergio_backup::BackupExtension::new(pool.clone())),
        Arc::new(convergio_multitenancy::MultitenancyExtension::new(
            pool.clone(),
        )),
        Arc::new(convergio_evidence::EvidenceExtension::new(pool.clone())),
        Arc::new(convergio_observatory::ObservatoryExtension::new(
            pool.clone(),
        )),
    ]
}

#[tokio::main]
async fn main() {
    // 1. Logging
    let _guard = convergio_telemetry::logging::init();
    tracing::info!(
        version = env!("CARGO_PKG_VERSION"),
        "convergio daemon starting"
    );

    // 2. Config
    let config = load_config();
    let port = config.daemon.port;
    let config = Arc::new(RwLock::new(config));

    // 3. Database
    let db_path =
        convergio_types::platform_paths::convergio_data_dir().join("convergio.db");
    if let Some(parent) = db_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let pool = create_pool(&db_path).expect("database pool creation failed");

    // 4. Core migrations
    {
        let conn = pool.get().expect("db connection for migrations");
        let core = convergio_db::core_tables::core_migrations();
        convergio_db::migration::apply_migrations(&conn, "convergio-db", &core)
            .expect("core migrations failed");
    }

    // 5. Register extensions
    let extensions = register_extensions(pool.clone());
    let ctx = AppContext::new();

    // 6. Extension migrations
    {
        let conn = pool.get().expect("db connection for ext migrations");
        for ext in &extensions {
            let manifest = ext.manifest();
            let migrations = ext.migrations();
            if !migrations.is_empty() {
                match convergio_db::migration::apply_migrations(
                    &conn,
                    &manifest.id,
                    &migrations,
                ) {
                    Ok(n) if n > 0 => {
                        tracing::info!(
                            module = manifest.id,
                            applied = n,
                            "migrations applied"
                        );
                    }
                    Err(e) => {
                        tracing::error!(
                            module = %manifest.id,
                            error = %e,
                            "migration failed"
                        );
                    }
                    _ => {}
                }
            }
        }
    }

    // 7. Health + metrics
    let health = Arc::new(HealthRegistry::new());
    let metrics = Arc::new(MetricsCollector::new());

    // 8. Start extensions
    for ext in &extensions {
        if let Err(e) = ext.on_start(&ctx) {
            tracing::warn!(
                module = %ext.manifest().id,
                error = %e,
                "extension on_start failed"
            );
        }
    }

    // 9. Build router
    let state = ServerState::new(pool, config, health, metrics, false);
    let router = build_router(state, &extensions, &ctx);

    // 10. Serve
    let bind = format!("0.0.0.0:{port}");
    tracing::info!(extensions = extensions.len(), bind = %bind, "daemon ready");

    if let Err(e) = run_server(&bind, router).await {
        tracing::error!("server failed: {e:?}");
        std::process::exit(1);
    }

    // 11. Shutdown
    for ext in extensions.iter().rev() {
        let _ = ext.on_shutdown();
    }
    tracing::info!("daemon stopped");
}
