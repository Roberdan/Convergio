//! Core delegation pipeline — copy files, spawn agent, monitor, sync back.

use crate::queries::{complete_delegation, update_delegation_status, update_remote_path};
use crate::types::{DelegationStatus, DelegationStep, PipelineConfig};
use convergio_db::pool::ConnPool;
use convergio_file_transport::types::{TransferDirection, TransferRequest};
use convergio_mesh::peers_registry::peers_conf_path_from_env;
use convergio_mesh::peers_types::PeersRegistry;
use std::path::Path;

type BoxErr = Box<dyn std::error::Error + Send + Sync>;

/// Info returned by a successful pipeline run, used to start the monitor.
pub struct PipelineResult {
    pub ssh_target: String,
    pub tmux_session: String,
    pub tmux_window: String,
    pub remote_path: String,
}

/// Resolve the SSH target string for a peer from the peers registry.
fn resolve_ssh_target(peer_name: &str) -> Result<String, BoxErr> {
    let conf_path = peers_conf_path_from_env();
    let registry = PeersRegistry::load(Path::new(&conf_path))?;
    let peer_cfg = registry
        .peers
        .get(peer_name)
        .ok_or_else(|| format!("peer '{peer_name}' not found in peers.conf"))?;
    if peer_cfg.ssh_alias.is_empty() {
        Ok(format!("{}@{}", peer_cfg.user, peer_cfg.tailscale_ip))
    } else {
        Ok(peer_cfg.ssh_alias.clone())
    }
}

/// Run the full delegation pipeline: copy -> spawn -> set Running.
/// Returns info needed to start the remote monitor.
pub async fn run_delegation_pipeline(
    pool: &ConnPool,
    delegation_id: &str,
    plan_id: i64,
    peer_name: &str,
    config: &PipelineConfig,
) -> Result<PipelineResult, BoxErr> {
    let ssh_target = resolve_ssh_target(peer_name)?;
    let remote_path = format!("{}/{}", config.remote_base, delegation_id);

    // Step 1: Copy files to peer
    update_delegation_status(
        pool,
        delegation_id,
        &DelegationStatus::CopyingFiles,
        &DelegationStep::FileCopy,
    )?;
    let push_req = TransferRequest {
        source_path: config.project_root.clone(),
        dest_path: remote_path.clone(),
        peer_name: peer_name.to_string(),
        ssh_target: ssh_target.clone(),
        direction: TransferDirection::Push,
        exclude_patterns: config.exclude_patterns.clone(),
    };
    let push_result =
        convergio_file_transport::rsync::execute_rsync(&push_req, &ssh_target).await?;
    if let convergio_file_transport::types::TransferStatus::Failed(msg) = &push_result.status {
        let err = DelegationStatus::Failed(format!("file copy failed: {msg}"));
        update_delegation_status(pool, delegation_id, &err, &DelegationStep::FileCopy)?;
        return Err(format!("file copy failed: {msg}").into());
    }
    if let Ok(conn) = pool.get() {
        let _ = convergio_file_transport::transfer::record_transfer(&conn, &push_result, &push_req);
    }

    // Step 2: Spawn agent on peer
    update_delegation_status(
        pool,
        delegation_id,
        &DelegationStatus::Spawning,
        &DelegationStep::Spawn,
    )?;
    let tmux_session = format!("cvg-{delegation_id}");
    let tmux_window = format!("plan-{plan_id}");
    crate::remote_spawn::spawn_on_peer(
        &ssh_target,
        &remote_path,
        plan_id,
        &tmux_session,
        &tmux_window,
    )
    .await?;

    // Step 3: Running — monitoring happens asynchronously
    update_delegation_status(
        pool,
        delegation_id,
        &DelegationStatus::Running,
        &DelegationStep::Execute,
    )?;
    update_remote_path(pool, delegation_id, &remote_path)?;
    tracing::info!(delegation_id, peer_name, "delegation running on peer");
    Ok(PipelineResult {
        ssh_target,
        tmux_session,
        tmux_window,
        remote_path,
    })
}

/// Sync results back from the remote peer after completion.
pub async fn sync_back(
    pool: &ConnPool,
    delegation_id: &str,
    peer_name: &str,
    config: &PipelineConfig,
) -> Result<(), BoxErr> {
    let ssh_target = resolve_ssh_target(peer_name)?;
    let remote_path = format!("{}/{}", config.remote_base, delegation_id);

    update_delegation_status(
        pool,
        delegation_id,
        &DelegationStatus::SyncingBack,
        &DelegationStep::SyncBack,
    )?;
    let pull_req = TransferRequest {
        source_path: remote_path,
        dest_path: config.project_root.clone(),
        peer_name: peer_name.to_string(),
        ssh_target: ssh_target.clone(),
        direction: TransferDirection::Pull,
        exclude_patterns: config.exclude_patterns.clone(),
    };
    convergio_file_transport::rsync::execute_rsync(&pull_req, &ssh_target).await?;
    update_delegation_status(
        pool,
        delegation_id,
        &DelegationStatus::Done,
        &DelegationStep::Complete,
    )?;
    complete_delegation(pool, delegation_id)?;
    Ok(())
}
