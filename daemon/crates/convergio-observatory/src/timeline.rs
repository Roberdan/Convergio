//! Timeline API — cross-org event chronology with compound filters.

use rusqlite::{params, Connection};

use crate::types::{EventSource, TimelineEvent};

/// Parameters for inserting a new timeline event.
pub struct NewEvent<'a> {
    pub source: &'a EventSource,
    pub event_type: &'a str,
    pub actor: &'a str,
    pub org_id: Option<&'a str>,
    pub node_id: Option<&'a str>,
    pub summary: &'a str,
    pub details_json: Option<&'a str>,
}

/// Insert a new timeline event.
pub fn record_event(conn: &Connection, evt: &NewEvent<'_>) -> Result<i64, rusqlite::Error> {
    conn.execute(
        "INSERT INTO obs_timeline (source, event_type, actor, org_id, node_id, \
         summary, details_json) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        params![
            evt.source.to_string(),
            evt.event_type,
            evt.actor,
            evt.org_id,
            evt.node_id,
            evt.summary,
            evt.details_json
        ],
    )?;
    Ok(conn.last_insert_rowid())
}

/// Query parameters for timeline filtering.
pub struct TimelineFilter<'a> {
    pub org_id: Option<&'a str>,
    pub source: Option<&'a str>,
    pub event_type: Option<&'a str>,
    pub node_id: Option<&'a str>,
    pub since: Option<&'a str>,
    pub until: Option<&'a str>,
    pub limit: u32,
}

impl<'a> Default for TimelineFilter<'a> {
    fn default() -> Self {
        Self {
            org_id: None,
            source: None,
            event_type: None,
            node_id: None,
            since: None,
            until: None,
            limit: 100,
        }
    }
}

fn push_filter(
    sql: &mut String,
    binds: &mut Vec<Box<dyn rusqlite::types::ToSql>>,
    col: &str,
    val: Option<&str>,
    op: &str,
    idx: &mut u32,
) {
    if let Some(v) = val {
        sql.push_str(&format!(" AND {col} {op} ?{}", *idx));
        binds.push(Box::new(v.to_string()));
        *idx += 1;
    }
}

/// Query the timeline with compound filters.
pub fn query_timeline(
    conn: &Connection,
    filter: &TimelineFilter<'_>,
) -> Result<Vec<TimelineEvent>, rusqlite::Error> {
    let mut sql = String::from(
        "SELECT id, source, event_type, actor, org_id, node_id, \
         summary, details_json, created_at FROM obs_timeline WHERE 1=1",
    );
    let mut binds: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();
    let mut idx = 1u32;

    push_filter(&mut sql, &mut binds, "org_id", filter.org_id, "=", &mut idx);
    push_filter(&mut sql, &mut binds, "source", filter.source, "=", &mut idx);
    push_filter(
        &mut sql,
        &mut binds,
        "event_type",
        filter.event_type,
        "=",
        &mut idx,
    );
    push_filter(
        &mut sql,
        &mut binds,
        "node_id",
        filter.node_id,
        "=",
        &mut idx,
    );
    push_filter(
        &mut sql,
        &mut binds,
        "created_at",
        filter.since,
        ">=",
        &mut idx,
    );
    push_filter(
        &mut sql,
        &mut binds,
        "created_at",
        filter.until,
        "<=",
        &mut idx,
    );

    let limit = filter.limit.min(500);
    sql.push_str(&format!(" ORDER BY created_at DESC LIMIT {limit}"));

    let refs: Vec<&dyn rusqlite::types::ToSql> = binds.iter().map(|b| &**b).collect();
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map(refs.as_slice(), |row| {
        Ok(TimelineEvent {
            id: row.get(0)?,
            source: EventSource::from_str_value(&row.get::<_, String>(1)?),
            event_type: row.get(2)?,
            actor: row.get(3)?,
            org_id: row.get(4)?,
            node_id: row.get(5)?,
            summary: row.get(6)?,
            details_json: row.get(7)?,
            created_at: row.get(8)?,
        })
    })?;
    rows.collect()
}
