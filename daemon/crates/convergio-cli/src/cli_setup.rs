// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// `cvg setup` — interactive first-run wizard for Convergio Platform.

use crate::cli_error::CliError;
use crate::cli_setup_steps as steps;
use dialoguer::{Confirm, Input, Select};

const ROLES: [&str; 3] = ["standalone", "coordinator", "worker"];
const ROLE_DESC: [&str; 3] = [
    "standalone  — single node, no mesh networking",
    "coordinator — orchestrates workers, hosts plans DB",
    "worker      — receives delegated tasks from coordinator",
];

/// Run the interactive setup wizard. `--defaults` skips all prompts.
pub(crate) async fn handle_setup(defaults: bool) -> Result<(), CliError> {
    if defaults {
        return write_defaults().await;
    }

    println!();
    println!("Welcome to Convergio Setup!");
    println!("===========================");
    println!();

    // Step 1: Node name
    let detected = steps::detect_hostname();
    let node_name: String = Input::new()
        .with_prompt("Step 1/5 — Node name")
        .default(detected)
        .interact_text()
        .map_err(|e| CliError::InvalidInput(e.to_string()))?;

    // Step 2: Role
    println!();
    println!("Step 2/5 — Node role");
    for desc in &ROLE_DESC {
        println!("  {desc}");
    }
    let role_idx = Select::new()
        .with_prompt("Select role")
        .items(&ROLES)
        .default(0)
        .interact()
        .map_err(|e| CliError::InvalidInput(e.to_string()))?;
    let role = ROLES[role_idx];

    // Step 3: Network
    println!();
    println!("Step 3/5 — Network");
    let use_tailscale = detect_network();

    // Step 4: AI Model / API key
    println!();
    println!("Step 4/5 — AI Model");
    configure_api_key().await?;

    // Step 5: Write config + summary
    println!();
    println!("Step 5/5 — Writing configuration...");
    let config_path = crate::paths::config_path();
    let content = steps::render_config(&node_name, role, use_tailscale);
    if let Some(parent) = config_path.parent() {
        std::fs::create_dir_all(parent).map_err(CliError::Io)?;
    }
    std::fs::write(&config_path, &content).map_err(CliError::Io)?;

    // Generate default aliases if not present
    let aliases_path = config_path
        .parent()
        .unwrap_or(std::path::Path::new("."))
        .join("aliases.toml");
    if !aliases_path.exists() {
        let defaults = crate::cli_ask::generate_default_aliases();
        std::fs::write(&aliases_path, &defaults).map_err(CliError::Io)?;
        println!("Agent aliases written to {}", aliases_path.display());
    }

    println!();
    println!("Configuration saved to {}", config_path.display());
    println!();
    print_summary(&node_name, role, use_tailscale);

    // Offer mesh join for worker/coordinator roles with Tailscale
    if role != "standalone" && use_tailscale {
        println!();
        offer_mesh_join().await?;
    }

    println!();
    println!("Next steps:");
    println!("  cvg serve    — start the daemon");
    println!("  cvg status   — check platform health");
    println!();
    Ok(())
}

// ---------------------------------------------------------------------------
// Network detection (Step 3)
// ---------------------------------------------------------------------------

fn detect_network() -> bool {
    if let Some(ts) = steps::detect_tailscale() {
        println!(
            "  Tailscale detected (IP: {})",
            if ts.ip.is_empty() { "unknown" } else { &ts.ip }
        );
        if !ts.peers.is_empty() {
            println!("  Peers found:");
            for peer in &ts.peers {
                println!("    - {peer}");
            }
        }
        let use_ts = Confirm::new()
            .with_prompt("  Use Tailscale for mesh networking?")
            .default(true)
            .interact()
            .unwrap_or(true);
        return use_ts;
    }

    let ifaces = steps::detect_lan_interfaces();
    if !ifaces.is_empty() {
        println!("  LAN mode (interfaces: {})", ifaces.join(", "));
    } else {
        println!("  LAN mode (no Tailscale detected)");
    }
    false
}

// ---------------------------------------------------------------------------
// API key configuration (Step 4)
// ---------------------------------------------------------------------------

async fn configure_api_key() -> Result<(), CliError> {
    if let Ok(key) = std::env::var("ANTHROPIC_API_KEY") {
        if !key.is_empty() {
            println!(
                "  Claude API key found in environment. \
                 Default model: claude-sonnet-4-6"
            );
            return Ok(());
        }
    }

    let key: String = Input::new()
        .with_prompt("  Enter Anthropic API key (or press Enter to skip)")
        .allow_empty(true)
        .interact_text()
        .map_err(|e| CliError::InvalidInput(e.to_string()))?;

    if key.is_empty() {
        println!(
            "  Skipped. Set ANTHROPIC_API_KEY later or run \
             `cvg setup` again."
        );
        return Ok(());
    }

    print!("  Validating key... ");
    if steps::validate_api_key(&key).await {
        println!("OK");
        steps::write_env_file(&key).map_err(CliError::Io)?;
        println!("  Key saved to ~/.convergio/env");
    } else {
        println!("FAILED");
        println!(
            "  Key could not be validated. Saving anyway — \
             check it later."
        );
        steps::write_env_file(&key).map_err(CliError::Io)?;
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Defaults mode (--defaults)
// ---------------------------------------------------------------------------

async fn write_defaults() -> Result<(), CliError> {
    let node_name = steps::detect_hostname();
    let ts = steps::detect_tailscale().is_some();
    let content = steps::render_config(&node_name, "standalone", ts);
    let config_path = crate::paths::config_path();
    if let Some(parent) = config_path.parent() {
        std::fs::create_dir_all(parent).map_err(CliError::Io)?;
    }
    std::fs::write(&config_path, &content).map_err(CliError::Io)?;
    println!("Default config written to {}", config_path.display());
    print_summary(&node_name, "standalone", ts);
    Ok(())
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

fn print_summary(name: &str, role: &str, tailscale: bool) {
    let net = if tailscale { "tailscale" } else { "lan" };
    println!("Summary:");
    println!("  Node:      {name}");
    println!("  Role:      {role}");
    println!("  Network:   {net}");
    println!("  Model:     claude-sonnet-4-6");
}

async fn offer_mesh_join() -> Result<(), CliError> {
    let join = Confirm::new()
        .with_prompt("Join an existing mesh now?")
        .default(true)
        .interact()
        .unwrap_or(false);
    if !join {
        println!("  Skipped. Run `cvg mesh join <coordinator_url>` later.");
        return Ok(());
    }
    let url: String = Input::new()
        .with_prompt("Coordinator URL (e.g. http://100.89.245.79:8420)")
        .interact_text()
        .map_err(|e| CliError::InvalidInput(e.to_string()))?;
    crate::cli_mesh_join::handle_mesh_join(&url).await
}
