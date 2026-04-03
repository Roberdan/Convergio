// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Agent history CLI handler — extracted from cli_agent_format.rs (250-line limit).

use crate::cli_error::CliError;

pub(crate) async fn handle_history(
    api_url: &str,
    since: Option<String>,
    until: Option<String>,
    status: Option<String>,
    model: Option<String>,
    limit: Option<u32>,
) -> Result<(), CliError> {
    // Default: 7 days for CLI (API defaults to 30)
    let since_val = since.unwrap_or_else(|| {
        let dt = chrono::Utc::now() - chrono::Duration::days(7);
        dt.format("%Y-%m-%dT%H:%M:%S").to_string()
    });
    let lim = limit.unwrap_or(20).min(500);
    let mut pairs = url::form_urlencoded::Serializer::new(String::new());
    pairs.append_pair("since", &since_val);
    if let Some(ref u) = until {
        pairs.append_pair("until", u);
    }
    if let Some(ref s) = status {
        pairs.append_pair("status", s);
    }
    if let Some(ref m) = model {
        pairs.append_pair("model", m);
    }
    pairs.append_pair("limit", &lim.to_string());
    let qs = pairs.finish();
    let url = format!("{api_url}/api/agents/history?{qs}");
    let client = reqwest::Client::new();
    let resp = client
        .get(&url)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;
    let rows: Vec<serde_json::Value> = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
    if rows.is_empty() {
        println!("No agent history found.");
        return Ok(());
    }
    print_history_table(&rows);
    Ok(())
}

fn print_history_table(rows: &[serde_json::Value]) {
    println!(
        "{:<28} {:<18} {:<11} {:>8} {:>9} {:>8} STARTED",
        "AGENT", "MODEL", "STATUS", "DURATION", "TOKENS", "COST",
    );
    for r in rows {
        let agent = r["agent_id"].as_str().unwrap_or("-");
        let mdl = r["model"].as_str().unwrap_or("-");
        let st = r["status"].as_str().unwrap_or("-");
        let dur = format_duration(r["duration_s"].as_f64());
        let tok_in = r["tokens_in"].as_i64().unwrap_or(0);
        let tok_out = r["tokens_out"].as_i64().unwrap_or(0);
        let tokens = format!("{}/{}", tok_in, tok_out);
        let cost = r["cost_usd"].as_f64().unwrap_or(0.0);
        let cost_s = format!("${cost:.3}");
        let started = r["started_at"].as_str().unwrap_or("-");
        let agent_short = truncate(agent, 27);
        let mdl_short = truncate(mdl, 17);
        println!(
            "{:<28} {:<18} {:<11} {:>8} {:>9} {:>8} {}",
            agent_short, mdl_short, st, dur, tokens, cost_s, started
        );
    }
    println!("\n{} record(s)", rows.len());
}

fn format_duration(secs: Option<f64>) -> String {
    match secs {
        Some(s) if s >= 3600.0 => format!("{:.0}h{:.0}m", s / 3600.0, (s % 3600.0) / 60.0),
        Some(s) if s >= 60.0 => format!("{:.0}m{:.0}s", s / 60.0, s % 60.0),
        Some(s) => format!("{:.0}s", s),
        None => "-".to_string(),
    }
}

fn truncate(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}~", &s[..max - 1])
    }
}
