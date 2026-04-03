use super::*;
use rusqlite::Connection;

fn setup() -> Connection {
    let conn = Connection::open_in_memory().unwrap();
    convergio_db::migration::ensure_registry(&conn).unwrap();
    convergio_db::migration::apply_migrations(&conn, "prompts", &crate::schema::migrations())
        .unwrap();
    conn
}

#[test]
fn register_and_search() {
    let conn = setup();
    register_skill(
        &conn,
        &SkillInput {
            agent: "elena".into(),
            host: "m5max".into(),
            capability: "legal-review".into(),
            confidence: 0.95,
            description: "Contract clause analysis".into(),
        },
    )
    .unwrap();
    register_skill(
        &conn,
        &SkillInput {
            agent: "baccio".into(),
            host: "m1pro".into(),
            capability: "code-review".into(),
            confidence: 0.9,
            description: "Rust code review".into(),
        },
    )
    .unwrap();
    let legal = search_skills(
        &conn,
        &SkillQuery {
            capability: Some("legal-review".into()),
            ..Default::default()
        },
    )
    .unwrap();
    assert_eq!(legal.len(), 1);
    assert_eq!(legal[0].agent, "elena");
}

#[test]
fn find_best_agent_by_capability() {
    let conn = setup();
    register_skill(
        &conn,
        &SkillInput {
            agent: "junior".into(),
            host: "h1".into(),
            capability: "testing".into(),
            confidence: 0.4,
            description: "Basic testing".into(),
        },
    )
    .unwrap();
    register_skill(
        &conn,
        &SkillInput {
            agent: "senior".into(),
            host: "h1".into(),
            capability: "testing".into(),
            confidence: 0.95,
            description: "Deep testing".into(),
        },
    )
    .unwrap();
    let best = find_best_agent(&conn, "testing").unwrap().unwrap();
    assert_eq!(best.agent, "senior");
}

#[test]
fn confidence_update_weighted() {
    let conn = setup();
    register_skill(
        &conn,
        &SkillInput {
            agent: "worker".into(),
            host: "h".into(),
            capability: "deploy".into(),
            confidence: 0.5,
            description: "Deployment".into(),
        },
    )
    .unwrap();
    // 0.8 * 0.5 + 0.2 * 1.0 = 0.6
    update_confidence(&conn, "worker", "h", "deploy", 1.0).unwrap();
    let skills = search_skills(
        &conn,
        &SkillQuery {
            agent: Some("worker".into()),
            ..Default::default()
        },
    )
    .unwrap();
    let conf = skills[0].confidence;
    assert!((conf - 0.6).abs() < 0.01, "expected ~0.6, got {conf}");
}

#[test]
fn unregister_removes_all() {
    let conn = setup();
    register_skill(
        &conn,
        &SkillInput {
            agent: "temp".into(),
            host: "h".into(),
            capability: "s1".into(),
            confidence: 0.5,
            description: "Skill 1".into(),
        },
    )
    .unwrap();
    register_skill(
        &conn,
        &SkillInput {
            agent: "temp".into(),
            host: "h".into(),
            capability: "s2".into(),
            confidence: 0.5,
            description: "Skill 2".into(),
        },
    )
    .unwrap();
    let removed = unregister_agent(&conn, "temp", "h").unwrap();
    assert_eq!(removed, 2);
}
