//! Model router — semantic routing with budget awareness.
//!
//! Selects the best model based on: classified tier, health status,
//! budget constraints, and cost optimization. Replaces the static
//! fallback chain (t1/t2/t3/t4) with intelligent routing.

use std::collections::HashMap;

use crate::budget;
use crate::classifier;
use crate::types::{
    InferenceConstraints, InferenceRequest, InferenceResponse, InferenceTier, ModelEndpoint,
    ModelProvider, RoutingDecision,
};

/// Routes inference requests to the best available model.
///
/// Selection pipeline:
/// 1. Classify request tier (semantic, not static)
/// 2. Apply budget constraints (downgrade if near limit)
/// 3. Filter by health and tier coverage
/// 4. Sort by preference: local first, then by cost
/// 5. Build fallback chain from remaining candidates
pub struct ModelRouter {
    models: HashMap<String, ModelEndpoint>,
}

impl ModelRouter {
    pub fn new() -> Self {
        Self {
            models: HashMap::new(),
        }
    }

    /// Register a model endpoint. Replaces existing entry with same name.
    pub fn register_model(&mut self, endpoint: ModelEndpoint) {
        self.models.insert(endpoint.name.clone(), endpoint);
    }

    /// Update health status for a named model.
    pub fn set_health(&mut self, name: &str, healthy: bool) {
        if let Some(ep) = self.models.get_mut(name) {
            ep.healthy = healthy;
        }
    }

    /// Return all registered model names.
    pub fn model_names(&self) -> Vec<String> {
        self.models.keys().cloned().collect()
    }

    /// Route a request, applying semantic classification and budget awareness.
    /// Returns Err when no healthy model covers the effective tier.
    pub fn route(
        &self,
        request: &InferenceRequest,
        budget_downgrade: bool,
    ) -> Result<(InferenceResponse, RoutingDecision), String> {
        let classified_tier = classifier::classify(request);

        let effective_tier = if budget_downgrade {
            budget::downgrade_tier(classified_tier.clone())
        } else {
            classified_tier.clone()
        };

        let decision = self.select(&effective_tier, &request.constraints, budget_downgrade)?;

        let response = InferenceResponse {
            content: format!(
                "[routed to {}] {}",
                decision.selected_model, &request.prompt
            ),
            model_used: decision.selected_model.clone(),
            latency_ms: 0,
            tokens_used: request.max_tokens,
            cost: 0.0,
        };

        Ok((response, decision))
    }

    /// Build a routing decision for the given tier and constraints.
    fn select(
        &self,
        tier: &InferenceTier,
        constraints: &InferenceConstraints,
        budget_downgrade: bool,
    ) -> Result<RoutingDecision, String> {
        let mut candidates: Vec<&ModelEndpoint> = self
            .models
            .values()
            .filter(|ep| ep.healthy && ep.tier_range.0 <= *tier && ep.tier_range.1 >= *tier)
            .collect();

        if candidates.is_empty() {
            return Err(format!("no healthy model for tier {:?}", tier));
        }

        // Sort: local first, then by input cost ascending
        candidates.sort_by(|a, b| {
            let local_a = if a.provider == ModelProvider::Local {
                0
            } else {
                1
            };
            let local_b = if b.provider == ModelProvider::Local {
                0
            } else {
                1
            };
            local_a.cmp(&local_b).then(
                a.cost_per_1k_input
                    .partial_cmp(&b.cost_per_1k_input)
                    .unwrap(),
            )
        });

        // Apply max_cost constraint if set
        if let Some(max_cost) = constraints.max_cost {
            candidates.retain(|ep| ep.cost_per_1k_input <= max_cost);
            if candidates.is_empty() {
                return Err("no model within cost constraint".to_string());
            }
        }

        let selected = candidates[0];
        let fallback_chain: Vec<String> = candidates[1..].iter().map(|e| e.name.clone()).collect();

        let reason = if budget_downgrade {
            format!("tier {:?} (downgraded from budget pressure)", tier)
        } else {
            format!("tier {:?} → best candidate by cost/locality", tier)
        };

        Ok(RoutingDecision {
            selected_model: selected.name.clone(),
            reason,
            effective_tier: tier.label().to_string(),
            fallback_chain,
            budget_remaining: None,
        })
    }
}

impl Default for ModelRouter {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
#[path = "router_tests.rs"]
mod tests;
