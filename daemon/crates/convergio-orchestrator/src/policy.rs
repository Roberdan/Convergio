// Autonomous execution policy — risk-based auto-progression control.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum RiskLevel {
    Low,
    Medium,
    High,
    Critical,
}

impl RiskLevel {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Low => "LOW",
            Self::Medium => "MEDIUM",
            Self::High => "HIGH",
            Self::Critical => "CRITICAL",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_uppercase().as_str() {
            "LOW" => Some(Self::Low),
            "MEDIUM" => Some(Self::Medium),
            "HIGH" => Some(Self::High),
            "CRITICAL" => Some(Self::Critical),
            _ => None,
        }
    }
}

/// Classify risk from task_type and effort_level (1-5 scale).
pub fn classify(task_type: &str, effort_level: u8) -> RiskLevel {
    let t = task_type.to_lowercase();

    if t.contains("migration") || t.contains("breaking") {
        return RiskLevel::Critical;
    }
    if t.contains("security") || t.contains("arch") || effort_level >= 3 {
        return RiskLevel::High;
    }
    if t.contains("config") || t.contains("doc") || t.contains("test") || effort_level <= 1 {
        return RiskLevel::Low;
    }
    RiskLevel::Medium
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionPolicy {
    pub id: Option<i64>,
    pub project_id: String,
    pub risk_level: String,
    pub auto_progress: bool,
    pub require_human: bool,
    pub require_double_validation: bool,
}

impl ExecutionPolicy {
    pub fn default_for(project_id: &str, risk: RiskLevel) -> Self {
        let (auto_progress, require_human, require_double_validation) = match risk {
            RiskLevel::Low | RiskLevel::Medium => (true, false, false),
            RiskLevel::High => (false, true, false),
            RiskLevel::Critical => (false, true, true),
        };
        Self {
            id: None,
            project_id: project_id.to_string(),
            risk_level: risk.as_str().to_string(),
            auto_progress,
            require_human,
            require_double_validation,
        }
    }
}

/// Load all policies for a project, inserting defaults where missing.
pub fn load_or_default(
    conn: &rusqlite::Connection,
    project_id: &str,
) -> rusqlite::Result<Vec<ExecutionPolicy>> {
    for risk in [
        RiskLevel::Low,
        RiskLevel::Medium,
        RiskLevel::High,
        RiskLevel::Critical,
    ] {
        let policy = ExecutionPolicy::default_for(project_id, risk);
        conn.execute(
            "INSERT OR IGNORE INTO execution_policy \
             (project_id, risk_level, auto_progress, require_human, require_double_validation) \
             VALUES (?1, ?2, ?3, ?4, ?5)",
            rusqlite::params![
                policy.project_id,
                policy.risk_level,
                policy.auto_progress,
                policy.require_human,
                policy.require_double_validation,
            ],
        )?;
    }

    let mut stmt = conn.prepare(
        "SELECT id, project_id, risk_level, auto_progress, require_human, \
         require_double_validation FROM execution_policy WHERE project_id = ?1 \
         ORDER BY CASE risk_level WHEN 'LOW' THEN 0 WHEN 'MEDIUM' THEN 1 \
         WHEN 'HIGH' THEN 2 WHEN 'CRITICAL' THEN 3 ELSE 4 END",
    )?;

    let rows = stmt.query_map(rusqlite::params![project_id], |row| {
        Ok(ExecutionPolicy {
            id: row.get(0)?,
            project_id: row.get(1)?,
            risk_level: row.get(2)?,
            auto_progress: row.get(3)?,
            require_human: row.get(4)?,
            require_double_validation: row.get(5)?,
        })
    })?;

    rows.collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn classify_critical() {
        assert_eq!(classify("data_migration", 1), RiskLevel::Critical);
        assert_eq!(classify("breaking_change", 2), RiskLevel::Critical);
    }

    #[test]
    fn classify_high() {
        assert_eq!(classify("security_audit", 2), RiskLevel::High);
        assert_eq!(classify("feature", 3), RiskLevel::High);
    }

    #[test]
    fn classify_low() {
        assert_eq!(classify("config_update", 1), RiskLevel::Low);
        assert_eq!(classify("docs", 2), RiskLevel::Low);
    }

    #[test]
    fn classify_medium() {
        assert_eq!(classify("feature_code", 2), RiskLevel::Medium);
    }

    #[test]
    fn default_policy_critical() {
        let p = ExecutionPolicy::default_for("p1", RiskLevel::Critical);
        assert!(!p.auto_progress);
        assert!(p.require_human);
        assert!(p.require_double_validation);
    }

    #[test]
    fn risk_ordering() {
        assert!(RiskLevel::Low < RiskLevel::Critical);
    }

    #[test]
    fn load_or_default_seeds() {
        let conn = rusqlite::Connection::open_in_memory().unwrap();
        for m in crate::schema::migrations() {
            conn.execute_batch(m.up).unwrap();
        }
        let policies = load_or_default(&conn, "test-project").unwrap();
        assert_eq!(policies.len(), 4);
    }
}
