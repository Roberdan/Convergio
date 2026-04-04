use super::*;
use rusqlite::Connection;

fn setup() -> Connection {
    let conn = Connection::open_in_memory().unwrap();
    for m in crate::schema::migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    for m in crate::schema_tracking::tracking_migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    for m in crate::schema_evaluation::evaluation_migrations() {
        conn.execute_batch(m.up).unwrap();
    }
    conn
}

fn sample_eval(plan_id: i64) -> PlanEvaluation {
    PlanEvaluation {
        id: 0,
        plan_id,
        evaluator: "system".to_string(),
        tasks_total: 10,
        tasks_completed: 8,
        tasks_failed: 2,
        false_positives: 1,
        false_negatives: 1,
        precision: 0.89,
        recall: 0.89,
        f1_score: 0.89,
        total_cost_usd: 1.50,
        total_duration_secs: 3600,
        evaluated_at: String::new(),
    }
}

#[test]
fn test_record_and_list_evaluation() {
    let conn = setup();
    let eval = sample_eval(1);
    let id = record_evaluation(&conn, &eval).unwrap();
    assert!(id > 0);

    let list = list_evaluations(&conn, Some(1), 10);
    assert_eq!(list.len(), 1);
    assert_eq!(list[0].plan_id, 1);
    assert_eq!(list[0].tasks_total, 10);

    // Different plan_id should not appear
    let _ = record_evaluation(&conn, &sample_eval(2)).unwrap();
    let list1 = list_evaluations(&conn, Some(1), 10);
    assert_eq!(list1.len(), 1);
    let all = list_evaluations(&conn, None, 10);
    assert_eq!(all.len(), 2);
}

#[test]
fn test_compute_thor_accuracy() {
    let conn = setup();
    // 3 correct approvals, 1 false positive, 1 false negative
    record_review_outcome(&conn, 1, 1, "approved", "success").unwrap();
    record_review_outcome(&conn, 1, 2, "approved", "success").unwrap();
    record_review_outcome(&conn, 1, 3, "approved", "success").unwrap();
    record_review_outcome(&conn, 1, 4, "approved", "failure").unwrap();
    record_review_outcome(&conn, 1, 5, "rejected", "success").unwrap();

    let acc = compute_thor_accuracy(&conn);
    assert_eq!(acc.total_reviews, 5);
    assert_eq!(acc.correct_approvals, 3);
    assert_eq!(acc.false_positives, 1);
    assert_eq!(acc.false_negatives, 1);
    // precision = 3/(3+1) = 0.75
    assert!((acc.precision - 0.75).abs() < 0.001);
    // recall = 3/(3+1) = 0.75
    assert!((acc.recall - 0.75).abs() < 0.001);
    // f1 = 2*0.75*0.75/(0.75+0.75) = 0.75
    assert!((acc.f1 - 0.75).abs() < 0.001);
}

#[test]
fn test_planner_success_rate() {
    let conn = setup();
    // No data: rate should be 0
    assert!((planner_success_rate(&conn) - 0.0).abs() < 0.001);

    let _ = record_evaluation(&conn, &sample_eval(1)).unwrap();
    // 8/10 = 0.8
    assert!((planner_success_rate(&conn) - 0.8).abs() < 0.001);
}

#[test]
fn test_review_outcome_tracking() {
    let conn = setup();
    record_review_outcome(&conn, 1, 10, "approved", "success").unwrap();
    record_review_outcome(&conn, 1, 11, "rejected", "failure").unwrap();
    record_review_outcome(&conn, 2, 20, "approved", "failure").unwrap();

    let all = list_review_outcomes(&conn, None);
    assert_eq!(all.len(), 3);

    let plan1 = list_review_outcomes(&conn, Some(1));
    assert_eq!(plan1.len(), 2);
    assert!(plan1[0].is_correct || plan1[1].is_correct);

    let plan2 = list_review_outcomes(&conn, Some(2));
    assert_eq!(plan2.len(), 1);
    assert!(!plan2[0].is_correct);
}
