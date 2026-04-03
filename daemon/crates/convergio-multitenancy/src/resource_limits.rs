//! Resource limits — per-org soft tracking (cgroup-like, no OS enforcement).
//!
//! Tracks CPU seconds, memory, storage, agent count, and API call rate.
//! Emits warnings/violations when limits are exceeded but does not kill processes.

use crate::types::{OrgId, ResourceLimits, ResourceUsage, TenancyError, ViolationType};
use chrono::Utc;
use rusqlite::Connection;

/// Set or update resource limits for an org.
pub fn set_limits(conn: &Connection, limits: &ResourceLimits) -> Result<(), TenancyError> {
    conn.execute(
        "INSERT INTO mt_resource_limits
         (org_id, max_cpu_seconds_per_hour, max_memory_mb, max_storage_mb,
          max_concurrent_agents, max_api_calls_per_minute)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)
         ON CONFLICT(org_id) DO UPDATE SET
          max_cpu_seconds_per_hour = ?2, max_memory_mb = ?3,
          max_storage_mb = ?4, max_concurrent_agents = ?5,
          max_api_calls_per_minute = ?6",
        rusqlite::params![
            limits.org_id.0,
            limits.max_cpu_seconds_per_hour,
            limits.max_memory_mb,
            limits.max_storage_mb,
            limits.max_concurrent_agents,
            limits.max_api_calls_per_minute,
        ],
    )
    .map_err(|e| TenancyError::Db(format!("set_limits: {e}")))?;
    Ok(())
}

/// Get resource limits for an org.
pub fn get_limits(
    conn: &Connection,
    org_id: &OrgId,
) -> Result<Option<ResourceLimits>, TenancyError> {
    let result = conn.query_row(
        "SELECT max_cpu_seconds_per_hour, max_memory_mb, max_storage_mb,
                max_concurrent_agents, max_api_calls_per_minute
         FROM mt_resource_limits WHERE org_id = ?1",
        [&org_id.0],
        |row| {
            Ok(ResourceLimits {
                org_id: org_id.clone(),
                max_cpu_seconds_per_hour: row.get(0)?,
                max_memory_mb: row.get(1)?,
                max_storage_mb: row.get(2)?,
                max_concurrent_agents: row.get(3)?,
                max_api_calls_per_minute: row.get(4)?,
            })
        },
    );
    match result {
        Ok(l) => Ok(Some(l)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(TenancyError::Db(e.to_string())),
    }
}

/// Record a resource usage snapshot for an org.
pub fn record_usage(conn: &Connection, usage: &ResourceUsage) -> Result<(), TenancyError> {
    conn.execute(
        "INSERT INTO mt_resource_usage
         (org_id, cpu_seconds_this_hour, memory_mb_current,
          storage_mb_current, active_agents, api_calls_this_minute)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        rusqlite::params![
            usage.org_id.0,
            usage.cpu_seconds_this_hour,
            usage.memory_mb_current,
            usage.storage_mb_current,
            usage.active_agents,
            usage.api_calls_this_minute,
        ],
    )
    .map_err(|e| TenancyError::Db(format!("record_usage: {e}")))?;
    Ok(())
}

/// Get the latest usage snapshot for an org.
pub fn latest_usage(
    conn: &Connection,
    org_id: &OrgId,
) -> Result<Option<ResourceUsage>, TenancyError> {
    let result = conn.query_row(
        "SELECT cpu_seconds_this_hour, memory_mb_current, storage_mb_current,
                active_agents, api_calls_this_minute
         FROM mt_resource_usage WHERE org_id = ?1
         ORDER BY recorded_at DESC LIMIT 1",
        [&org_id.0],
        |row| {
            Ok(ResourceUsage {
                org_id: org_id.clone(),
                cpu_seconds_this_hour: row.get(0)?,
                memory_mb_current: row.get(1)?,
                storage_mb_current: row.get(2)?,
                active_agents: row.get(3)?,
                api_calls_this_minute: row.get(4)?,
                recorded_at: Utc::now(),
            })
        },
    );
    match result {
        Ok(u) => Ok(Some(u)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(TenancyError::Db(e.to_string())),
    }
}

/// Check if any resource limit is exceeded. Returns list of violations.
pub fn check_limits(conn: &Connection, org_id: &OrgId) -> Result<Vec<String>, TenancyError> {
    let limits = match get_limits(conn, org_id)? {
        Some(l) => l,
        None => return Ok(vec![]),
    };
    let usage = match latest_usage(conn, org_id)? {
        Some(u) => u,
        None => return Ok(vec![]),
    };
    let mut violations = Vec::new();
    if usage.cpu_seconds_this_hour > limits.max_cpu_seconds_per_hour as f64 {
        violations.push(format!(
            "CPU: {:.0}/{} seconds/hour",
            usage.cpu_seconds_this_hour, limits.max_cpu_seconds_per_hour
        ));
    }
    if usage.memory_mb_current > limits.max_memory_mb as f64 {
        violations.push(format!(
            "Memory: {:.0}/{} MB",
            usage.memory_mb_current, limits.max_memory_mb
        ));
    }
    if usage.storage_mb_current > limits.max_storage_mb as f64 {
        violations.push(format!(
            "Storage: {:.0}/{} MB",
            usage.storage_mb_current, limits.max_storage_mb
        ));
    }
    if usage.active_agents > limits.max_concurrent_agents {
        violations.push(format!(
            "Agents: {}/{}",
            usage.active_agents, limits.max_concurrent_agents
        ));
    }
    if usage.api_calls_this_minute > limits.max_api_calls_per_minute {
        violations.push(format!(
            "API rate: {}/{}",
            usage.api_calls_this_minute, limits.max_api_calls_per_minute
        ));
    }
    if !violations.is_empty() {
        record_violation(conn, org_id, &violations.join("; "))?;
    }
    Ok(violations)
}

/// Record an isolation violation.
fn record_violation(conn: &Connection, org_id: &OrgId, details: &str) -> Result<(), TenancyError> {
    conn.execute(
        "INSERT INTO mt_isolation_violations
         (org_id, violation_type, details, blocked)
         VALUES (?1, ?2, ?3, 0)",
        rusqlite::params![
            org_id.0,
            ViolationType::ResourceLimitExceeded.to_string(),
            details
        ],
    )
    .map_err(|e| TenancyError::Db(format!("record_violation: {e}")))?;
    tracing::warn!(org = %org_id, details, "resource limit exceeded");
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn setup() -> Connection {
        let c = Connection::open_in_memory().unwrap();
        c.execute_batch("PRAGMA journal_mode=WAL;").unwrap();
        for m in crate::schema::migrations() {
            c.execute_batch(m.up).unwrap();
        }
        c
    }

    #[test]
    fn set_and_get_limits() {
        let conn = setup();
        let limits = ResourceLimits::default_for(OrgId("acme".into()));
        set_limits(&conn, &limits).unwrap();
        let got = get_limits(&conn, &OrgId("acme".into())).unwrap().unwrap();
        assert_eq!(got.max_concurrent_agents, 20);
    }

    #[test]
    fn record_and_check_within_limits() {
        let conn = setup();
        let org = OrgId("good".into());
        set_limits(&conn, &ResourceLimits::default_for(org.clone())).unwrap();
        let usage = ResourceUsage {
            org_id: org.clone(),
            cpu_seconds_this_hour: 100.0,
            memory_mb_current: 512.0,
            storage_mb_current: 1000.0,
            active_agents: 5,
            api_calls_this_minute: 10,
            recorded_at: Utc::now(),
        };
        record_usage(&conn, &usage).unwrap();
        let violations = check_limits(&conn, &org).unwrap();
        assert!(violations.is_empty());
    }

    #[test]
    fn detect_exceeded_limits() {
        let conn = setup();
        let org = OrgId("heavy".into());
        let mut limits = ResourceLimits::default_for(org.clone());
        limits.max_concurrent_agents = 2;
        set_limits(&conn, &limits).unwrap();
        let usage = ResourceUsage {
            org_id: org.clone(),
            cpu_seconds_this_hour: 10.0,
            memory_mb_current: 256.0,
            storage_mb_current: 100.0,
            active_agents: 5,
            api_calls_this_minute: 1,
            recorded_at: Utc::now(),
        };
        record_usage(&conn, &usage).unwrap();
        let violations = check_limits(&conn, &org).unwrap();
        assert_eq!(violations.len(), 1);
        assert!(violations[0].contains("Agents"));
    }
}
