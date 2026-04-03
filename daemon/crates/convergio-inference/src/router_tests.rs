use super::*;

fn ep(
    name: &str,
    provider: ModelProvider,
    low: InferenceTier,
    high: InferenceTier,
    cost: f64,
) -> ModelEndpoint {
    ModelEndpoint {
        name: name.into(),
        provider,
        url: format!("http://localhost/{name}"),
        cost_per_1k_input: cost,
        cost_per_1k_output: cost * 3.0,
        tier_range: (low, high),
        healthy: true,
    }
}

fn req(tier: Option<InferenceTier>) -> InferenceRequest {
    InferenceRequest {
        prompt: "test prompt".into(),
        max_tokens: 256,
        tier_hint: tier,
        agent_id: "elena".into(),
        org_id: Some("legal-corp".into()),
        plan_id: Some(42),
        constraints: InferenceConstraints {
            max_latency_ms: None,
            max_cost: None,
        },
    }
}

#[test]
fn routes_to_cheapest_local_model() {
    let mut router = ModelRouter::new();
    router.register_model(ep(
        "haiku",
        ModelProvider::Cloud,
        InferenceTier::T1Trivial,
        InferenceTier::T2Standard,
        0.25,
    ));
    router.register_model(ep(
        "gemma",
        ModelProvider::Local,
        InferenceTier::T1Trivial,
        InferenceTier::T2Standard,
        0.0,
    ));

    let (resp, decision) = router
        .route(&req(Some(InferenceTier::T1Trivial)), false)
        .unwrap();
    assert_eq!(resp.model_used, "gemma");
    assert!(decision.fallback_chain.contains(&"haiku".to_string()));
}

#[test]
fn skips_unhealthy_models() {
    let mut router = ModelRouter::new();
    let mut broken = ep(
        "broken",
        ModelProvider::Local,
        InferenceTier::T1Trivial,
        InferenceTier::T4Critical,
        0.0,
    );
    broken.healthy = false;
    router.register_model(broken);
    router.register_model(ep(
        "healthy",
        ModelProvider::Cloud,
        InferenceTier::T1Trivial,
        InferenceTier::T4Critical,
        1.0,
    ));

    let (resp, _) = router
        .route(&req(Some(InferenceTier::T2Standard)), false)
        .unwrap();
    assert_eq!(resp.model_used, "healthy");
}

#[test]
fn error_when_no_model_for_tier() {
    let mut router = ModelRouter::new();
    router.register_model(ep(
        "tiny",
        ModelProvider::Local,
        InferenceTier::T1Trivial,
        InferenceTier::T1Trivial,
        0.0,
    ));

    let result = router.route(&req(Some(InferenceTier::T4Critical)), false);
    assert!(result.is_err());
}

#[test]
fn budget_downgrade_changes_tier() {
    let mut router = ModelRouter::new();
    router.register_model(ep(
        "haiku",
        ModelProvider::Cloud,
        InferenceTier::T1Trivial,
        InferenceTier::T2Standard,
        0.25,
    ));
    router.register_model(ep(
        "opus",
        ModelProvider::Cloud,
        InferenceTier::T3Complex,
        InferenceTier::T4Critical,
        15.0,
    ));

    // T3 with downgrade -> T2, should use haiku not opus
    let (resp, decision) = router
        .route(&req(Some(InferenceTier::T3Complex)), true)
        .unwrap();
    assert_eq!(resp.model_used, "haiku");
    assert_eq!(decision.effective_tier, "t2");
}

#[test]
fn health_update_toggles_availability() {
    let mut router = ModelRouter::new();
    router.register_model(ep(
        "model-a",
        ModelProvider::Local,
        InferenceTier::T1Trivial,
        InferenceTier::T4Critical,
        0.0,
    ));
    router.set_health("model-a", false);
    assert!(router
        .route(&req(Some(InferenceTier::T2Standard)), false)
        .is_err());

    router.set_health("model-a", true);
    let (resp, _) = router
        .route(&req(Some(InferenceTier::T2Standard)), false)
        .unwrap();
    assert_eq!(resp.model_used, "model-a");
}
