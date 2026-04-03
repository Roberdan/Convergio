// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// `cvg api list` — print all daemon HTTP API endpoints grouped by domain.

pub fn api_list_text() -> &'static str {
    r#"Convergio Daemon API — all endpoints (port 8420)

PLANS
  GET  /api/plan-db/list[?status=&limit=]    List plans (all by default)
  GET  /api/plan-db/json/:plan_id           Compact plan JSON
  GET  /api/plan-db/execution-tree/:plan_id Execution tree (waves + tasks)
  GET  /api/plan-db/context/:plan_id        Full plan context for execution
  GET  /api/plan-db/execution-context/:plan_id  Next pending task + prompt
  GET  /api/plan-db/drift-check/:plan_id    Plan staleness check
  GET  /api/plan-db/readiness/:plan_id      Pre-execution readiness
  POST /api/plan-db/create                  Create new plan
  POST /api/plan-db/import                  Import spec YAML
  POST /api/plan-db/start/:plan_id          Start plan execution
  POST /api/plan-db/complete/:plan_id       Mark plan complete
  POST /api/plan-db/cancel/:plan_id         Cancel plan
  POST /api/plan-db/approve/:plan_id        Approve for execution
  POST /api/plan-db/task/update             Update task status
  POST /api/plan-db/set-worktree/:plan_id   Set plan worktree path
  POST /api/plans/:plan_id/validate         Thor wave validation

WAVES & KB
  POST /api/plan-db/wave/create             Create wave
  POST /api/plan-db/wave/update             Update wave
  GET  /api/plan-db/kb-search               Search knowledge base
  POST /api/plan-db/kb-write                Write KB entry

AGENTS
  GET  /api/agents/catalog                  List agent catalog
  POST /api/agents/sync                     Sync agent catalog
  POST /api/agents/enable                   Enable agent
  POST /api/agents/disable                  Disable agent
  POST /api/agents/create                   Create agent entry
  POST /api/agent/interrupt                 Interrupt blocked agent
  POST /api/task/reschedule                 Reschedule task to another node

MESH & PEERS
  GET  /api/peers                           List peers
  POST /api/peers                           Create peer
  GET  /api/peers/discover                  Discover Tailscale peers
  POST /api/peers/ssh-check                 Check SSH connectivity
  GET  /api/crdt/status                     CRDT sync status
  POST /api/crdt/force-sync                 Force CRDT sync
  GET  /api/crdt/peers                      CRDT peer list

KERNEL & HEALTH
  GET  /api/health                          Health check
  GET  /api/health/deep                     Deep health check (all subsystems)
  GET  /api/node/readiness                  Node readiness (10 checks)

CHAT
  GET  /api/chat/models                     Available chat models
  GET  /api/chat/sessions                   List chat sessions
  POST /api/chat/message                    Send chat message
  POST /api/chat/approve                    Approve chat action
  POST /api/chat/execute                    Execute chat command
  PUT  /api/chat/requirement                Upsert requirement

CHANNELS
  GET  /api/channels                        List channels
  POST /api/channels/:name/send             Send message to channel
  GET  /api/channels/:name/health           Channel health

CAPABILITIES
  GET  /api/capabilities/list               List capabilities
  POST /api/capabilities/invoke             Invoke capability
  POST /api/capabilities/register           Register capability
  GET  /api/capabilities/schema/:name       Get capability schema
  PUT  /api/capabilities/permissions        Update permissions

METRICS & TRACKING
  GET  /api/metrics/summary                 Metrics summary
  GET  /api/metrics/cost                    Cost breakdown
  GET  /api/metrics/run/:id                 Run metrics
  POST /api/tracking/tokens                 Track token usage
  POST /api/tracking/agent-activity         Track agent activity
  POST /api/tracking/session-state          Track session state
  POST /api/tracking/compaction             Record compaction

WORKSPACE
  GET  /api/workspace/list                  List workspaces
  POST /api/workspace/create                Create workspace

AUDIT & REPOS
  GET  /api/audit/project/:project_id       Project audit
  GET  /api/repositories/:name              Show repository

SSE & WEBSOCKET
  GET  /api/chat/stream/:sid                Chat stream (SSE)
  GET  /api/mesh/action/stream              Mesh action stream (SSE)
  GET  /api/plan/preflight                  Plan preflight (SSE)
  GET  /api/plan/delegate                   Plan delegate (SSE)
  GET  /api/plan/start                      Plan start (SSE)
  GET  /ws/brain                            Brain WebSocket
  GET  /ws/dashboard                        Dashboard WebSocket
  GET  /ws/pty                              PTY WebSocket

OPENCLAW
  GET  /api/openclaw/agents                 List OpenClaw agents
  POST /api/openclaw/invoke                 Invoke OpenClaw agent
"#
}

pub fn print_api_list() {
    print!("{}", api_list_text());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn api_list_covers_major_domains() {
        let text = api_list_text();
        let domains = [
            "PLANS",
            "AGENTS",
            "MESH & PEERS",
            "KERNEL & HEALTH",
            "CHAT",
            "CHANNELS",
            "CAPABILITIES",
            "METRICS",
        ];
        for domain in domains {
            assert!(text.contains(domain), "must cover domain '{domain}'");
        }
    }

    #[test]
    fn api_list_includes_methods() {
        let text = api_list_text();
        assert!(text.contains("GET "), "must include GET methods");
        assert!(text.contains("POST"), "must include POST methods");
        assert!(text.contains("PUT "), "must include PUT methods");
    }
}
