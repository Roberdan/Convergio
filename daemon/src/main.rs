//! Convergio daemon — wires extensions together and launches the server.

use convergio_db::pool::{create_pool, ConnPool};
use convergio_server::config_watcher::spawn_config_watcher;
use convergio_server::{build_router, load_config, run_server, ServerState};
use convergio_telemetry::health::HealthRegistry;
use convergio_telemetry::metrics::MetricsCollector;
use convergio_types::extension::{AppContext, Extension};
use std::sync::{Arc, RwLock};
use tokio::sync::Notify;

fn register_extensions(
    pool: ConnPool,
    event_bus: Arc<convergio_ipc::sse::EventBus>,
) -> Vec<Arc<dyn Extension>> {
    let notify = Arc::new(Notify::new());

    vec![
        // Infrastructure
        Arc::new(convergio_db::DbExtension),
        Arc::new(convergio_ipc::IpcExtension::with_bus(
            pool.clone(),
            event_bus,
        )),
        Arc::new(convergio_mesh::ext::MeshExtension::new(pool.clone())),
        // Platform services
        Arc::new(convergio_orchestrator::OrchestratorExtension::new(
            pool.clone(),
            notify,
        )),
        Arc::new(convergio_inference::InferenceExtension::new(pool.clone())),
        Arc::new(convergio_agents::AgentsCatalogExtension::new(pool.clone())),
        Arc::new(convergio_prompts::ext::PromptsExtension::new(pool.clone())),
        Arc::new(convergio_agent_runtime::AgentRuntimeExtension::new(
            pool.clone(),
        )),
        // Extensions
        Arc::new(convergio_kernel::KernelExtension::new(pool.clone())),
        Arc::new(convergio_org::OrgExtension::new(pool.clone())),
        Arc::new(convergio_voice::VoiceExtension),
        // Ecosystem
        Arc::new(convergio_org_package::OrgPackageExtension::new(
            pool.clone(),
        )),
        Arc::new(convergio_http_bridge::HttpBridgeExtension::new()),
        // Platform tools
        Arc::new(convergio_file_transport::FileTransportExtension::new(
            pool.clone(),
        )),
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
    // 0. Load env file (auth tokens, API keys)
    // Check ~/.convergio/env first (legacy), then data_dir/env
    let env_candidates = [
        dirs::home_dir().unwrap_or_default().join(".convergio/env"),
        convergio_types::platform_paths::convergio_data_dir().join("env"),
    ];
    for env_path in &env_candidates {
        if let Ok(contents) = std::fs::read_to_string(env_path) {
            for line in contents.lines() {
                let line = line.trim();
                if line.is_empty() || line.starts_with('#') {
                    continue;
                }
                if let Some((k, v)) = line.split_once('=') {
                    if std::env::var(k.trim()).is_err() {
                        std::env::set_var(k.trim(), v.trim());
                    }
                }
            }
            break;
        }
    }

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

    // 2b. Config hot-reload watcher
    if let Err(e) = spawn_config_watcher(Arc::clone(&config)) {
        tracing::warn!("config watcher not started: {e}");
    }

    // 3. Database
    let db_path = convergio_types::platform_paths::convergio_data_dir().join("convergio.db");
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

    // 5. Register extensions (shared EventBus for domain events → SSE)
    let event_bus = Arc::new(convergio_ipc::sse::EventBus::new(1024));
    let mut extensions = register_extensions(pool.clone(), Arc::clone(&event_bus));

    // 5b. Wire depgraph with manifests from all registered extensions
    let manifests: Vec<_> = extensions.iter().map(|e| e.manifest()).collect();
    extensions.push(Arc::new(convergio_depgraph::DepgraphExtension::new(
        manifests,
    )));

    let mut ctx = AppContext::new();
    let sink: Arc<dyn convergio_types::events::DomainEventSink> = event_bus.clone();
    ctx.insert(sink);
    ctx.insert(Arc::clone(&event_bus));

    // 6. Extension migrations
    {
        let conn = pool.get().expect("db connection for ext migrations");
        for ext in &extensions {
            let manifest = ext.manifest();
            let migrations = ext.migrations();
            if !migrations.is_empty() {
                match convergio_db::migration::apply_migrations(&conn, &manifest.id, &migrations) {
                    Ok(n) if n > 0 => {
                        tracing::info!(module = manifest.id, applied = n, "migrations applied");
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

    // 7. Health + metrics — register extensions as health/metric sources
    let health = Arc::new(HealthRegistry::new());
    let metrics = Arc::new(MetricsCollector::new());
    for ext in &extensions {
        let manifest = ext.manifest();
        // Wrap each extension as a health check source
        let ext_clone = Arc::clone(ext);
        let name = manifest.id.clone();
        health.register(Arc::new(ExtHealthAdapter(name, ext_clone)));
    }
    for ext in &extensions {
        let manifest = ext.manifest();
        let ext_clone = Arc::clone(ext);
        let name = manifest.id.clone();
        metrics.register(Arc::new(ExtMetricAdapter(name, ext_clone)));
    }

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

    // 9. Build router — dev mode when no auth token configured
    let dev_mode = std::env::var("CONVERGIO_AUTH_TOKEN")
        .map(|v| v.is_empty())
        .unwrap_or(true);
    if dev_mode {
        tracing::info!("dev-mode enabled (no CONVERGIO_AUTH_TOKEN set)");
    }
    let shutdown_pool = pool.clone();
    let state = ServerState::new(pool, config, health, metrics, dev_mode);
    let router = build_router(state, &extensions, &ctx);

    // 10. Serve
    let bind = format!("0.0.0.0:{port}");
    tracing::info!(extensions = extensions.len(), bind = %bind, "daemon ready");

    if let Err(e) = run_server(&bind, router).await {
        tracing::error!("server failed: {e:?}");
        std::process::exit(1);
    }

    // 11. Shutdown
    // WAL checkpoint: flush pending writes to main DB before dropping pool
    if let Ok(conn) = shutdown_pool.get() {
        match conn.execute_batch("PRAGMA wal_checkpoint(TRUNCATE);") {
            Ok(()) => tracing::info!("WAL checkpoint completed"),
            Err(e) => tracing::warn!("WAL checkpoint failed: {e}"),
        }
    }
    for ext in extensions.iter().rev() {
        let _ = ext.on_shutdown();
    }
    tracing::info!("daemon stopped");
}

/// Adapter: wraps an Extension as a HealthCheck for the HealthRegistry.
struct ExtHealthAdapter(String, Arc<dyn Extension>);

impl convergio_telemetry::health::HealthCheck for ExtHealthAdapter {
    fn name(&self) -> &str {
        &self.0
    }
    fn check(&self) -> convergio_telemetry::health::ComponentHealth {
        let status = self.1.health();
        convergio_telemetry::health::ComponentHealth {
            name: self.0.clone(),
            status,
            message: None,
        }
    }
}

/// Adapter: wraps an Extension as a MetricSource for the MetricsCollector.
struct ExtMetricAdapter(String, Arc<dyn Extension>);

impl convergio_telemetry::metrics::MetricSource for ExtMetricAdapter {
    fn name(&self) -> &str {
        &self.0
    }
    fn collect(&self) -> Vec<convergio_types::extension::Metric> {
        self.1.metrics()
    }
}
