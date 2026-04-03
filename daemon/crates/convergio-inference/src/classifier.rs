//! Task complexity classifier — semantic tier assignment.
//!
//! Replaces the static t1/t2/t3/t4 mapping with keyword-based routing.
//! Priority: tier_hint > keyword analysis > prompt length heuristic.

use crate::types::{InferenceRequest, InferenceTier};

/// Classify an inference request into a tier.
///
/// WHY: semantic routing beats static chains — a short prompt asking for
/// "architecture review" should use a capable model, not the cheapest one.
pub fn classify(request: &InferenceRequest) -> InferenceTier {
    if let Some(hint) = &request.tier_hint {
        return hint.clone();
    }

    let prompt_lower = request.prompt.to_lowercase();
    let len = request.prompt.len();

    let base = base_tier_from_length(len);
    let delta = keyword_delta(&prompt_lower);
    apply_delta(base, delta)
}

/// Base tier from prompt length.
fn base_tier_from_length(len: usize) -> InferenceTier {
    if len < 100 {
        InferenceTier::T1Trivial
    } else if len < 500 {
        InferenceTier::T2Standard
    } else if len < 2000 {
        InferenceTier::T3Complex
    } else {
        InferenceTier::T4Critical
    }
}

/// Count keyword-based tier adjustments.
fn keyword_delta(prompt: &str) -> i32 {
    const BOOSTERS: &[&str] = &[
        "architecture",
        "security",
        "review",
        "refactor",
        "design",
        "critical",
    ];
    const REDUCERS: &[&str] = &["format", "list", "simple", "rename", "typo"];

    let boost = BOOSTERS.iter().filter(|&&kw| prompt.contains(kw)).count() as i32;
    let reduce = REDUCERS.iter().filter(|&&kw| prompt.contains(kw)).count() as i32;
    boost - reduce
}

/// Apply delta to tier, clamping to valid range.
fn apply_delta(tier: InferenceTier, delta: i32) -> InferenceTier {
    let idx = tier_to_index(&tier);
    let clamped = (idx + delta).clamp(0, 3);
    index_to_tier(clamped)
}

fn tier_to_index(tier: &InferenceTier) -> i32 {
    match tier {
        InferenceTier::T1Trivial => 0,
        InferenceTier::T2Standard => 1,
        InferenceTier::T3Complex => 2,
        InferenceTier::T4Critical => 3,
    }
}

fn index_to_tier(idx: i32) -> InferenceTier {
    match idx {
        0 => InferenceTier::T1Trivial,
        1 => InferenceTier::T2Standard,
        2 => InferenceTier::T3Complex,
        _ => InferenceTier::T4Critical,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::InferenceConstraints;

    fn make_request(prompt: &str, hint: Option<InferenceTier>) -> InferenceRequest {
        InferenceRequest {
            prompt: prompt.to_string(),
            max_tokens: 256,
            tier_hint: hint,
            agent_id: "test-agent".into(),
            org_id: None,
            plan_id: None,
            constraints: InferenceConstraints {
                max_latency_ms: None,
                max_cost: None,
            },
        }
    }

    #[test]
    fn hint_overrides_classification() {
        let req = make_request("hello", Some(InferenceTier::T4Critical));
        assert_eq!(classify(&req), InferenceTier::T4Critical);
    }

    #[test]
    fn short_prompt_is_trivial() {
        let req = make_request("fix typo", None);
        // "typo" reducer brings T1 down, but floor is T1
        assert_eq!(classify(&req), InferenceTier::T1Trivial);
    }

    #[test]
    fn security_keyword_boosts_tier() {
        let req = make_request("check security of the auth module", None);
        // len < 100 → T1, "security" +1 → T2
        assert_eq!(classify(&req), InferenceTier::T2Standard);
    }

    #[test]
    fn long_prompt_is_complex() {
        let req = make_request(&"x".repeat(1500), None);
        assert_eq!(classify(&req), InferenceTier::T3Complex);
    }

    #[test]
    fn very_long_prompt_is_critical() {
        let req = make_request(&"x".repeat(3000), None);
        assert_eq!(classify(&req), InferenceTier::T4Critical);
    }
}
