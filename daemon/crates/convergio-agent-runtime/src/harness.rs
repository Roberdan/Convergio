//! Harness engineering templates — baseline test, TASK.md header, init.sh.
//!
//! Implements the Anthropic harness pattern (adapted for Convergio):
//! - Baseline test before every session
//! - One feature at a time
//! - Agent reads from DB, not static files
//! - Thor uses a separate model for evaluation

use crate::types::{RuntimeError, RuntimeResult};
use std::path::Path;

/// Write init.sh baseline test script to the worktree.
/// Agent MUST run this before starting work. If it fails, fix first.
pub fn write_baseline_script(workspace: &Path) -> RuntimeResult<()> {
    let path = workspace.join("init.sh");
    std::fs::write(&path, BASELINE_SCRIPT)
        .map_err(|e| RuntimeError::Internal(format!("write init.sh: {e}")))?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = std::fs::metadata(&path)
            .map_err(|e| RuntimeError::Internal(format!("metadata init.sh: {e}")))?
            .permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&path, perms)
            .map_err(|e| RuntimeError::Internal(format!("chmod init.sh: {e}")))?;
    }
    Ok(())
}

/// Resolve the model for Thor evaluation (separate from coding agent).
/// Defaults to Sonnet — different from the typical Opus coding tier.
pub fn thor_model() -> String {
    std::env::var("CONVERGIO_THOR_MODEL").unwrap_or_else(|_| "claude-sonnet-4-6".to_string())
}

/// Header prepended to every TASK.md — delegation rules + harness rules.
pub const DELEGATION_HEADER: &str = "\
# REGOLE OPERATIVE (leggere PRIMA di iniziare)

## STEP 0: Baseline test (OBBLIGATORIO)
Prima di qualsiasi lavoro, esegui:
```bash
bash init.sh
```
Se fallisce, FIXA IL BASELINE prima di iniziare. Non lavorare su una base rotta.

## UNA feature alla volta
Lavora su UNA SOLA feature per sessione. Testala. Committala. Non tentare
di fare 5 cose in parallelo. Una feature = un commit = un risultato verificabile.

## Leggi dal DB, non da file .md
Il daemon ha un DB con plans/tasks/evidence/context. Usa la context API:
```bash
curl http://localhost:8420/api/agents/context/{agent_id}
```
NON leggere stato da file .md statici — il DB e' la source of truth.

## Risparmia token — DELEGA il lavoro meccanico
Tu sei il COORDINATORE. Non scrivere codice meccanico direttamente.
Per ogni task >50 righe che non richiede decisioni architetturali:
```bash
cd <worktree> && gh copilot --model claude-opus-4-6
```

## Regole
- Leggi AGENTS.md per tutte le regole
- Worktree isolato, max 250 righe/file
- cargo check + test + fmt prima di commit
- Loop chiuso: chi produce input? chi consuma output? l'utente lo vede?
- NO squash merge (repo setting: solo merge commit)";

const BASELINE_SCRIPT: &str = r#"#!/bin/bash
# Baseline test — run BEFORE starting any work.
# If this fails, fix the baseline first. Do NOT start new work on a broken base.
set -e

echo "=== Baseline: cargo check ==="
cd daemon && cargo check --workspace

echo "=== Baseline: cargo test ==="
cargo test --workspace

echo "=== Baseline: daemon health ==="
curl -sf http://localhost:8420/api/health || echo "WARN: daemon not reachable (ok if not running locally)"

echo "=== Baseline PASSED ==="
"#;

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn write_baseline_creates_init_sh() {
        let tmp = tempfile::tempdir().unwrap();
        write_baseline_script(tmp.path()).unwrap();
        let init = tmp.path().join("init.sh");
        assert!(init.exists());
        let content = fs::read_to_string(init).unwrap();
        assert!(content.contains("cargo check"));
        assert!(content.contains("cargo test"));
        assert!(content.contains("Baseline PASSED"));
    }

    #[test]
    fn delegation_header_has_harness_rules() {
        assert!(DELEGATION_HEADER.contains("UNA feature alla volta"));
        assert!(DELEGATION_HEADER.contains("init.sh"));
        assert!(DELEGATION_HEADER.contains("context API"));
    }

    #[test]
    fn thor_model_defaults_to_sonnet() {
        if std::env::var("CONVERGIO_THOR_MODEL").is_err() {
            assert!(thor_model().contains("sonnet"));
        }
    }
}
