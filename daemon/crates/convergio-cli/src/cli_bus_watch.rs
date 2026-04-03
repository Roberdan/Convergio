use crate::cli_error::CliError;
use futures_util::StreamExt;
use serde_json::Value;

const CYAN: &str = "\x1b[36m";
const WHITE: &str = "\x1b[37m";
const DIM: &str = "\x1b[2m";
const RESET: &str = "\x1b[0m";

pub async fn run_watch(name: &str, api_url: &str) -> Result<(), CliError> {
    let url = format!("{api_url}/api/ipc/stream?agent={name}");
    let resp = reqwest::Client::new()
        .get(&url)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("error connecting to daemon: {e}")))?;
    if !resp.status().is_success() {
        return Err(CliError::ApiCallFailed(format!(
            "watch request failed: {}",
            resp.status()
        )));
    }

    let mut stream = resp.bytes_stream();
    let mut buffer = String::new();
    while let Some(item) = stream.next().await {
        let chunk =
            item.map_err(|e| CliError::ApiCallFailed(format!("stream read error: {e}")))?;
        buffer.push_str(&String::from_utf8_lossy(&chunk));
        while let Some(pos) = buffer.find('\n') {
            let line = buffer[..pos].to_string();
            buffer.drain(..=pos);
            if let Some(out) = parse_sse_data_line(&line) {
                println!("{out}");
            }
        }
    }
    Ok(())
}

pub fn parse_sse_data_line(line: &str) -> Option<String> {
    let raw = line.trim();
    let data = raw.strip_prefix("data: ")?;
    let payload: Value = serde_json::from_str(data).ok()?;
    let from = payload.get("from")?.as_str()?;
    let to = payload.get("to")?.as_str()?;
    let content = payload.get("content")?.as_str()?;
    let ts = payload
        .get("ts")
        .and_then(Value::as_str)
        .unwrap_or("00:00:00");
    let hhmmss = chrono::DateTime::parse_from_rfc3339(ts)
        .map(|dt| dt.format("%H:%M:%S").to_string())
        .unwrap_or_else(|_| ts.to_string());
    Some(format!(
        "{DIM}[{hhmmss}]{RESET} {CYAN}{from}{RESET} → {CYAN}{to}{RESET}: {WHITE}{content}{RESET}"
    ))
}

#[cfg(test)]
mod tests {
    use super::parse_sse_data_line;

    #[test]
    fn parse_sse_data_line_formats_display_row() {
        let line = r#"data: {"from":"roberto","to":"priya","content":"Come stai?","ts":"2026-03-31T10:32:15Z"}"#;
        let formatted = parse_sse_data_line(line).expect("parsed");
        assert!(formatted.contains("[10:32:15]"));
        assert!(formatted.contains("roberto"));
        assert!(formatted.contains("priya"));
        assert!(formatted.contains("Come stai?"));
    }
}
