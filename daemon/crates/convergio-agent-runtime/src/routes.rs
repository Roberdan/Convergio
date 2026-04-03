//! API routes: GET /api/agents/runtime — live view of the runtime.

use std::sync::Arc;

use axum::extract::State;
use axum::response::Json;
use axum::routing::get;
use axum::Router;

use convergio_db::pool::ConnPool;

use crate::types::RuntimeView;

/// Shared state for runtime routes.
pub struct RuntimeState {
    pub pool: ConnPool,
}

/// Build the agent runtime API router.
pub fn runtime_routes(state: Arc<RuntimeState>) -> Router {
    Router::new()
        .route("/api/agents/runtime", get(handle_runtime_view))
        .with_state(state)
}

async fn handle_runtime_view(State(state): State<Arc<RuntimeState>>) -> Json<serde_json::Value> {
    let conn = match state.pool.get() {
        Ok(c) => c,
        Err(e) => {
            return Json(serde_json::json!({
                "error": { "code": "POOL_ERROR", "message": e.to_string() }
            }));
        }
    };

    let active_agents = crate::allocator::list_active(&conn, None).unwrap_or_default();
    let queue_depth = crate::scheduler::queue_depth_total(&conn).unwrap_or(0);
    let stale = crate::heartbeat::find_stale(&conn)
        .map(|s| s.len())
        .unwrap_or(0);

    // Aggregate budget info
    let (total_budget, total_spent) = conn
        .query_row(
            "SELECT COALESCE(SUM(budget_usd), 0.0), COALESCE(SUM(spent_usd), 0.0) \
             FROM art_agents WHERE stage IN ('running', 'borrowed', 'spawning')",
            [],
            |r| Ok((r.get::<_, f64>(0)?, r.get::<_, f64>(1)?)),
        )
        .unwrap_or((0.0, 0.0));

    let delegations_active: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM art_delegations WHERE returned = 0",
            [],
            |r| r.get(0),
        )
        .unwrap_or(0);

    let view = RuntimeView {
        active_agents,
        queue_depth,
        total_budget_usd: total_budget,
        total_spent_usd: total_spent,
        delegations_active: delegations_active as usize,
        stale_count: stale,
    };

    Json(serde_json::to_value(view).unwrap_or_default())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runtime_routes_builds() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let state = Arc::new(RuntimeState { pool });
        let _router = runtime_routes(state);
    }
}
