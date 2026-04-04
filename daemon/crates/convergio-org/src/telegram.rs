//! Telegram notification client.
//!
//! Sends notifications to Telegram via bot token and chat ID from env.
//! Config: CONVERGIO_TELEGRAM_BOT_TOKEN, CONVERGIO_TELEGRAM_CHAT_ID

use serde_json::json;
use std::env;

#[derive(Clone, Debug)]
pub struct TelegramClient {
    pub bot_token: String,
    pub chat_id: String,
}

impl TelegramClient {
    pub fn from_env() -> Result<Self, String> {
        let bot_token = env::var("CONVERGIO_TELEGRAM_BOT_TOKEN")
            .map_err(|_| "CONVERGIO_TELEGRAM_BOT_TOKEN not set".to_string())?;
        let chat_id = env::var("CONVERGIO_TELEGRAM_CHAT_ID")
            .map_err(|_| "CONVERGIO_TELEGRAM_CHAT_ID not set".to_string())?;
        Ok(TelegramClient { bot_token, chat_id })
    }

    pub async fn send(&self, text: &str) -> Result<(), String> {
        let url = format!("https://api.telegram.org/bot{}/sendMessage", self.bot_token);
        let payload = json!({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        });

        let client = reqwest::Client::new();
        let resp = client
            .post(&url)
            .json(&payload)
            .send()
            .await
            .map_err(|e| format!("Telegram API error: {}", e))?;

        if resp.status().is_success() {
            Ok(())
        } else {
            Err(format!("Telegram API returned {}", resp.status()))
        }
    }
}

pub fn format_notification(
    severity: &str,
    title: &str,
    message: Option<&str>,
    plan_id: Option<i64>,
) -> String {
    let emoji = match severity {
        "error" => "🔴",
        "warning" => "🟡",
        "success" => "🟢",
        _ => "🔵",
    };

    let mut text = format!("{} <b>{}</b>", emoji, html_escape(title));

    if let Some(msg) = message {
        if !msg.is_empty() {
            text.push_str(&format!("\n\n{}", html_escape(msg)));
        }
    }

    if let Some(pid) = plan_id {
        text.push_str(&format!("\n\n<code>Plan #{}</code>", pid));
    }

    text
}

fn html_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_notification_info() {
        let result = format_notification("info", "Hello", Some("World"), Some(123));
        assert!(result.contains("🔵"));
        assert!(result.contains("<b>Hello</b>"));
        assert!(result.contains("World"));
        assert!(result.contains("Plan #123"));
    }

    #[test]
    fn test_format_notification_error() {
        let result = format_notification("error", "Error", Some("Bad thing"), None);
        assert!(result.contains("🔴"));
        assert!(result.contains("<b>Error</b>"));
        assert!(result.contains("Bad thing"));
    }

    #[test]
    fn test_format_notification_no_message() {
        let result = format_notification("warning", "Alert", None, None);
        assert!(result.contains("🟡"));
        assert!(result.contains("<b>Alert</b>"));
        assert!(!result.contains("\n\n"));
    }

    #[test]
    fn test_html_escape() {
        let result = format_notification("info", "Test <tag>", Some("a & b"), None);
        assert!(result.contains("Test &lt;tag&gt;"));
        assert!(result.contains("a &amp; b"));
    }

    #[test]
    fn test_severity_emoji_mapping() {
        assert!(format_notification("success", "OK", None, None).starts_with("🟢"));
        assert!(format_notification("warning", "OK", None, None).starts_with("🟡"));
        assert!(format_notification("error", "OK", None, None).starts_with("🔴"));
        assert!(format_notification("info", "OK", None, None).starts_with("🔵"));
        assert!(format_notification("unknown", "OK", None, None).starts_with("🔵"));
    }

    #[tokio::test]
    async fn test_client_from_env_missing_token() {
        // Clear env vars for this test
        std::env::remove_var("CONVERGIO_TELEGRAM_BOT_TOKEN");
        let result = TelegramClient::from_env();
        assert!(result.is_err());
    }

    #[test]
    fn test_client_clone() {
        let client = TelegramClient {
            bot_token: "token123".to_string(),
            chat_id: "chat456".to_string(),
        };
        let cloned = client.clone();
        assert_eq!(cloned.bot_token, "token123");
        assert_eq!(cloned.chat_id, "chat456");
    }
}
