// Tests for cli_delegation: formatting, command parsing, start/cancel variants.
// Why: Verify table rendering, field extraction, and new delegation subcommands.

use super::*;
use clap::Parser;
use serde_json::json;

/// Wrapper for clap parsing tests — mirrors main CLI structure.
#[derive(Parser)]
struct TestCli {
    #[command(subcommand)]
    cmd: DelegationCommands,
}

fn parse_delegation(args: &[&str]) -> DelegationCommands {
    let mut full = vec!["cvg"];
    full.extend_from_slice(args);
    TestCli::parse_from(full).cmd
}

#[test]
fn parse_start_command() {
    let cmd = parse_delegation(&["start", "742", "--peer", "macProM1"]);
    match cmd {
        DelegationCommands::Start {
            plan_id,
            peer,
            no_wait,
        } => {
            assert_eq!(plan_id, 742);
            assert_eq!(peer, "macProM1");
            assert!(!no_wait, "no_wait should default to false");
        }
        _ => panic!("expected Start variant"),
    }
}

#[test]
fn parse_start_no_wait_flag() {
    let cmd = parse_delegation(&["start", "99", "--peer", "worker", "--no-wait"]);
    match cmd {
        DelegationCommands::Start {
            plan_id,
            peer,
            no_wait,
        } => {
            assert_eq!(plan_id, 99);
            assert_eq!(peer, "worker");
            assert!(no_wait, "no_wait should be true when --no-wait is passed");
        }
        _ => panic!("expected Start variant"),
    }
}

#[test]
fn parse_cancel_command() {
    let cmd = parse_delegation(&["cancel", "742"]);
    match cmd {
        DelegationCommands::Cancel { plan_id } => assert_eq!(plan_id, 742),
        _ => panic!("expected Cancel variant"),
    }
}

#[test]
fn format_progress_row_all_fields() {
    let data = json!({
        "peer": "worker-milan",
        "status": "running",
        "current_task": "T2-03",
        "last_update": "2026-03-26T15:00:00Z",
        "output_summary": "Implementing feature X"
    });
    let row = format_progress_row(&data);
    assert!(row.contains("worker-milan"), "peer name missing");
    assert!(row.contains("running"), "status missing");
    assert!(row.contains("T2-03"), "current_task missing");
    assert!(
        row.contains("Implementing feature X"),
        "output_summary missing"
    );
}

#[test]
fn format_progress_row_missing_fields_uses_defaults() {
    let data = json!({});
    let row = format_progress_row(&data);
    // Must not panic and must produce a non-empty line
    assert!(!row.is_empty());
}

#[test]
fn format_progress_header_has_columns() {
    let hdr = format_progress_header();
    assert!(hdr.contains("PEER"), "PEER column header missing");
    assert!(hdr.contains("STATUS"), "STATUS column header missing");
    assert!(hdr.contains("TASK"), "TASK column header missing");
    assert!(hdr.contains("LAST UPDATE"), "LAST UPDATE header missing");
}

#[test]
fn format_progress_table_empty_data_shows_none() {
    let out = format_progress_table(&json!({"ok": true, "delegations": []}));
    assert!(
        out.contains("No active delegations") || out.contains("none"),
        "expected empty state message, got: {out}"
    );
}

#[test]
fn format_progress_table_with_entries() {
    let data = json!({
        "ok": true,
        "delegations": [{
            "peer": "node-rome",
            "status": "running",
            "current_task": "T1-01",
            "last_update": "2026-03-26T10:00:00Z",
            "output_summary": "cargo check passed"
        }]
    });
    let out = format_progress_table(&data);
    assert!(out.contains("node-rome"));
    assert!(out.contains("T1-01"));
    assert!(out.contains("cargo check passed"));
}
