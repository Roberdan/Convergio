//! Policy engine — scoring, selection, and persistence of scheduler policies.

use rusqlite::{params, Connection};

use crate::types::{PeerCandidate, SchedulerPolicy, SchedulingRequest};

/// Score a peer for a scheduling request using the given policy weights.
pub fn score_peer(
    peer_name: &str,
    peer_caps: &[String],
    peer_load: f64,
    request: &SchedulingRequest,
    policy: &SchedulerPolicy,
) -> PeerCandidate {
    let required = &request.required_capabilities;
    let capabilities_match = if required.is_empty() {
        1.0
    } else {
        let matched = required.iter().filter(|r| peer_caps.contains(r)).count();
        matched as f64 / required.len() as f64
    };

    let cost_score = match request.max_cost_usd {
        Some(max) if max > 0.0 => {
            // Estimate cost based on tier hint; simple heuristic for MVP.
            let estimated = estimate_tier_cost(request.tier_hint.as_deref());
            (1.0 - (estimated / max)).max(0.0)
        }
        _ => 0.5,
    };

    let load_score = 1.0 - peer_load.clamp(0.0, 1.0);

    let locality_bonus = match &request.preferred_locality {
        Some(loc) if loc == peer_name => 1.0,
        _ => 0.0,
    };

    let total = policy.weight_capability * capabilities_match
        + policy.weight_cost * cost_score
        + policy.weight_load * load_score
        + policy.weight_locality * locality_bonus;

    PeerCandidate {
        peer_name: peer_name.to_string(),
        score: total,
        capabilities_match,
        cost_score,
        load_score,
        locality_bonus,
    }
}

/// Select the best peer from a list of scored candidates.
pub fn select_best(candidates: Vec<PeerCandidate>) -> Option<PeerCandidate> {
    candidates.into_iter().max_by(|a, b| {
        a.score
            .partial_cmp(&b.score)
            .unwrap_or(std::cmp::Ordering::Equal)
    })
}

/// Return the default scheduling policy.
pub fn default_policy() -> SchedulerPolicy {
    SchedulerPolicy {
        id: 0,
        name: "default".to_string(),
        weight_capability: 0.4,
        weight_cost: 0.2,
        weight_load: 0.2,
        weight_locality: 0.2,
        privacy_enforce: true,
    }
}

/// Load a policy by name from DB, falling back to the default.
pub fn load_policy(conn: &Connection, name: &str) -> SchedulerPolicy {
    let result = conn.query_row(
        "SELECT id, name, weight_capability, weight_cost, weight_load, \
         weight_locality, privacy_enforce FROM scheduler_policies WHERE name = ?1",
        params![name],
        |row| {
            Ok(SchedulerPolicy {
                id: row.get(0)?,
                name: row.get(1)?,
                weight_capability: row.get(2)?,
                weight_cost: row.get(3)?,
                weight_load: row.get(4)?,
                weight_locality: row.get(5)?,
                privacy_enforce: row.get::<_, i32>(6)? != 0,
            })
        },
    );
    result.unwrap_or_else(|_| default_policy())
}

/// Save or update a policy in the DB (upsert on name).
pub fn save_policy(conn: &Connection, policy: &SchedulerPolicy) -> Result<(), rusqlite::Error> {
    conn.execute(
        "INSERT INTO scheduler_policies \
         (name, weight_capability, weight_cost, weight_load, weight_locality, privacy_enforce) \
         VALUES (?1, ?2, ?3, ?4, ?5, ?6) \
         ON CONFLICT(name) DO UPDATE SET \
         weight_capability = excluded.weight_capability, \
         weight_cost = excluded.weight_cost, \
         weight_load = excluded.weight_load, \
         weight_locality = excluded.weight_locality, \
         privacy_enforce = excluded.privacy_enforce",
        params![
            policy.name,
            policy.weight_capability,
            policy.weight_cost,
            policy.weight_load,
            policy.weight_locality,
            policy.privacy_enforce as i32,
        ],
    )?;
    Ok(())
}

/// Estimate cost in USD based on tier hint (simple heuristic).
fn estimate_tier_cost(tier: Option<&str>) -> f64 {
    match tier {
        Some("t1") => 0.01,
        Some("t2") => 0.05,
        Some("t3") => 0.20,
        Some("t4") => 1.00,
        _ => 0.10,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_request() -> SchedulingRequest {
        SchedulingRequest {
            task_id: 1,
            plan_id: 1,
            required_capabilities: vec!["gpu".into(), "voice".into()],
            preferred_locality: None,
            privacy_level: "public".into(),
            max_cost_usd: Some(1.0),
            tier_hint: Some("t2".into()),
        }
    }

    #[test]
    fn test_score_peer_all_caps_match() {
        let policy = default_policy();
        let req = sample_request();
        let caps = vec!["gpu".into(), "voice".into(), "compute".into()];
        let c = score_peer("darwin-m4", &caps, 0.2, &req, &policy);
        assert_eq!(c.capabilities_match, 1.0);
        assert!(c.score > 0.7, "expected high score, got {}", c.score);
    }

    #[test]
    fn test_score_peer_no_caps() {
        let policy = default_policy();
        let req = sample_request();
        let caps: Vec<String> = vec![];
        let c = score_peer("linux-a100", &caps, 0.5, &req, &policy);
        assert_eq!(c.capabilities_match, 0.0);
        assert!(c.score < 0.4, "expected low score, got {}", c.score);
    }

    #[test]
    fn test_select_best() {
        let candidates = vec![
            PeerCandidate {
                peer_name: "peer-a".into(),
                score: 0.6,
                capabilities_match: 1.0,
                cost_score: 0.5,
                load_score: 0.3,
                locality_bonus: 0.0,
            },
            PeerCandidate {
                peer_name: "peer-b".into(),
                score: 0.9,
                capabilities_match: 1.0,
                cost_score: 0.8,
                load_score: 0.8,
                locality_bonus: 1.0,
            },
        ];
        let best = select_best(candidates).unwrap();
        assert_eq!(best.peer_name, "peer-b");
    }

    #[test]
    fn test_default_policy_weights_sum_to_one() {
        let p = default_policy();
        let sum = p.weight_capability + p.weight_cost + p.weight_load + p.weight_locality;
        assert!((sum - 1.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_locality_bonus() {
        let policy = default_policy();
        let mut req = sample_request();
        req.preferred_locality = Some("darwin-m4".into());
        let caps = vec!["gpu".into(), "voice".into()];
        let local = score_peer("darwin-m4", &caps, 0.2, &req, &policy);
        let remote = score_peer("linux-a100", &caps, 0.2, &req, &policy);
        assert!(local.locality_bonus > remote.locality_bonus);
        assert!(local.score > remote.score);
    }

    #[test]
    fn test_save_and_load_policy() {
        let pool = convergio_db::pool::create_memory_pool().unwrap();
        let conn = pool.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "scheduler", &crate::schema::migrations())
            .unwrap();
        let mut policy = default_policy();
        policy.weight_capability = 0.6;
        policy.weight_cost = 0.1;
        policy.weight_load = 0.2;
        policy.weight_locality = 0.1;
        save_policy(&conn, &policy).unwrap();
        let loaded = load_policy(&conn, "default");
        assert!((loaded.weight_capability - 0.6).abs() < f64::EPSILON);
    }
}
