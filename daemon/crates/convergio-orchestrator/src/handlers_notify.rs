/// Send Telegram notification when plan completes. Non-blocking, fire-and-forget.
pub fn notify_plan_done(plan_id: i64, plan_name: &str) {
    let token = match std::env::var("CONVERGIO_TELEGRAM_BOT_TOKEN") {
        Ok(t) => t,
        Err(_) => return, // Telegram not configured — skip silently
    };
    let chat_id = match std::env::var("CONVERGIO_TELEGRAM_CHAT_ID") {
        Ok(c) => c,
        Err(_) => return,
    };

    let text = format!(
        "\u{1f7e2} <b>Plan completed</b>\n\n{}\n\n<code>Plan #{}</code>",
        html_escape(plan_name),
        plan_id
    );
    tokio::spawn(async move {
        let url = format!("https://api.telegram.org/bot{token}/sendMessage");
        let payload = serde_json::json!({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        });
        let client = reqwest::Client::new();
        if let Err(e) = client.post(&url).json(&payload).send().await {
            tracing::warn!("telegram notify failed for plan {plan_id}: {e}");
        }
    });
}

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}
