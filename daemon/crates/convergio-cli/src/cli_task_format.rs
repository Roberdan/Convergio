// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Human-readable formatting helpers for task CLI output.

/// Human-readable output for mechanical gate validation results.
pub fn print_mechanical_human(val: &serde_json::Value) {
    let mechanical = match val.get("mechanical") {
        Some(m) => m,
        None => {
            println!("{}", serde_json::to_string_pretty(val).unwrap_or_default());
            return;
        }
    };

    let status = mechanical
        .get("status")
        .and_then(serde_json::Value::as_str)
        .unwrap_or("UNKNOWN");
    let note = mechanical
        .get("note")
        .and_then(serde_json::Value::as_str)
        .unwrap_or("");

    println!("Mechanical Validation: {status}");
    println!();

    if let Some(gates) = mechanical.get("gates").and_then(|g| g.as_array()) {
        for gate in gates {
            let name = gate.get("gate").and_then(|g| g.as_str()).unwrap_or("?");
            let passed = gate
                .get("passed")
                .and_then(|p| p.as_bool())
                .unwrap_or(false);
            let icon = if passed { "PASS" } else { "FAIL" };
            println!("  [{icon}] {name}");
            if let Some(details) = gate.get("details").and_then(|d| d.as_array()) {
                for d in details {
                    if let Some(s) = d.as_str() {
                        println!("         {s}");
                    }
                }
            }
        }
    }

    if !note.is_empty() {
        println!();
        println!("{note}");
    }
}
