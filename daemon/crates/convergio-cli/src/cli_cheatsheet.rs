// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// `cvg cheatsheet` — print all available cvg commands grouped by domain.

pub fn cheatsheet_text() -> &'static str {
    r#"cvg cheatsheet — all available commands

ORGANIZATIONS
  cvg org list                         List orgs with status and budget
  cvg org show <slug>                  Org details (members, services, decisions)
  cvg org plans <slug>                 Plans belonging to an org
  cvg org chart [slug]                 Orgchart (global if no slug)
  cvg org create-org <name> --mission  Create org from mission
  cvg org create-org-from <path>       Create org from repo scan

PLANS
  cvg plan list [--status S] [--limit N] [--human]  List plans (all, newest first)
  cvg plan show <id> [--human]         Show plan details
  cvg plan tree <id> [--human]         Execution tree (waves + tasks)
  cvg plan create <proj> "name"        Create a new plan
  cvg plan import <id> spec.yaml       Import spec YAML
  cvg plan template                    Print example spec YAML
  cvg plan start <id>                  Begin execution
  cvg plan complete <id>               Mark complete (requires Thor + PR)
  cvg plan validate <id>               Thor wave-level validation
  cvg plan readiness <id>              Pre-execution checks
  cvg plan cancel <id> "reason"        Cancel with reason

TASKS & AGENTS
  cvg task update <id> <status>        Update task status
  cvg agent start "<name>"             Register agent session
  cvg agent complete "<name>"          Mark agent done
  cvg who agents                       Active agents across mesh

MESH
  cvg mesh status                      Peer topology
  cvg mesh heartbeat                   Send heartbeat
  cvg delegation start <plan> <peer>   Delegate plan to peer
  cvg delegation status <plan>         Delegation progress

KERNEL & VOICE
  cvg kernel status                    Kernel status
  cvg chat ["message"]                 Chat with Ali
  cvg voice start                      Start voice pipeline

RECOVERY
  cvg checkpoint save <plan_id>        Snapshot plan state
  cvg checkpoint restore <plan_id>     Restore from snapshot
  cvg reap worktrees [--dry-run]       Clean stale worktrees

OVERVIEW
  cvg status                           Platform overview
  cvg cheatsheet                       This help text
"#
}

pub fn print_cheatsheet() {
    print!("{}", cheatsheet_text());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cheatsheet_covers_major_domains() {
        let text = cheatsheet_text();
        let domains = [
            "ORGANIZATIONS",
            "PLANS",
            "TASKS & AGENTS",
            "MESH",
            "KERNEL & VOICE",
            "RECOVERY",
            "OVERVIEW",
        ];
        for domain in domains {
            assert!(text.contains(domain), "must cover domain '{domain}'");
        }
    }

    #[test]
    fn cheatsheet_includes_new_commands() {
        let text = cheatsheet_text();
        assert!(text.contains("cvg org chart"), "must include org chart");
        assert!(text.contains("cvg org plans"), "must include org plans");
        assert!(
            text.contains("cvg cheatsheet"),
            "must include self-reference"
        );
    }
}
