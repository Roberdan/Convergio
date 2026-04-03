use serde_json::{json, Value};

pub async fn run_ask(from: &str, to: &str, message: &str, timeout_secs: u64, api_url: &str) {
    let client = reqwest::Client::new();
    let body = json!({
        "from": from,
        "to": to,
        "message": message,
        "timeout_secs": timeout_secs
    });
    let url = format!("{api_url}/api/ipc/ask");
    match client.post(&url).json(&body).send().await {
        Ok(resp) => match resp.json::<Value>().await {
            Ok(payload) => match parse_ask_response(&payload) {
                Ok(reply) => println!("{reply}"),
                Err(err) => eprintln!("error: {err}"),
            },
            Err(e) => eprintln!("error: invalid ask response: {e}"),
        },
        Err(e) => eprintln!("error: ask request failed: {e}"),
    }
}

pub fn parse_ask_response(payload: &Value) -> Result<String, String> {
    if payload.get("ok").and_then(Value::as_bool) == Some(true) {
        let reply = payload
            .get("reply")
            .ok_or_else(|| "missing reply".to_string())?;
        let from = reply
            .get("from")
            .and_then(Value::as_str)
            .unwrap_or("unknown");
        let content = reply
            .get("content")
            .and_then(Value::as_str)
            .unwrap_or_default();
        return Ok(format!("{from}: {content}"));
    }
    let code = payload
        .get("error")
        .and_then(|e| e.get("code"))
        .and_then(Value::as_str)
        .unwrap_or("ERROR");
    let message = payload
        .get("error")
        .and_then(|e| e.get("message"))
        .and_then(Value::as_str)
        .unwrap_or("request failed");
    Err(format!("{code}: {message}"))
}

#[cfg(test)]
mod tests {
    use super::parse_ask_response;
    use serde_json::json;

    #[test]
    fn ask_timeout_returns_structured_error() {
        let payload = json!({
            "ok": false,
            "error": {
                "code": "TIMEOUT",
                "message": "No reply from priya within 120s"
            }
        });
        let err = parse_ask_response(&payload).expect_err("timeout expected");
        assert!(err.contains("TIMEOUT"));
        assert!(err.contains("No reply from priya within 120s"));
    }
}
