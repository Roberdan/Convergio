//! Resilience primitives — retry and circuit breaker configuration.
//!
//! These are pure config/state types. Runtime implementations
//! (async retry, breaker state machine) live in the crates that use them.

use std::time::Duration;

/// Configuration for retry with exponential backoff.
#[derive(Debug, Clone)]
pub struct RetryConfig {
    /// Additional attempts after the initial one (0 = no retry).
    pub max_retries: u32,
    /// Delay before the first retry.
    pub initial_delay: Duration,
    /// Maximum delay between retries (caps exponential growth).
    pub max_delay: Duration,
    /// Multiplier applied after each failure (e.g. 2.0 = double).
    pub backoff_factor: f64,
    /// When true, adds ±25% random jitter to each delay.
    pub jitter: bool,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_retries: 3,
            initial_delay: Duration::from_millis(100),
            max_delay: Duration::from_secs(10),
            backoff_factor: 2.0,
            jitter: true,
        }
    }
}

/// Circuit breaker states.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CircuitState {
    /// Normal operation — requests pass through.
    Closed,
    /// Too many failures — requests are rejected immediately.
    Open,
    /// Testing recovery — limited requests allowed.
    HalfOpen,
}

/// Configuration for a circuit breaker.
#[derive(Debug, Clone)]
pub struct CircuitBreakerConfig {
    /// Number of consecutive failures before opening.
    pub failure_threshold: u32,
    /// How long the circuit stays open before transitioning to half-open.
    pub reset_timeout: Duration,
    /// Number of successful requests in half-open needed to close.
    pub success_threshold: u32,
}

impl Default for CircuitBreakerConfig {
    fn default() -> Self {
        Self {
            failure_threshold: 5,
            reset_timeout: Duration::from_secs(30),
            success_threshold: 2,
        }
    }
}
