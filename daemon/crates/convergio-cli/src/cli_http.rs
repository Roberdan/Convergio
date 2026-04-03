// Copyright (c) 2026 Roberto D'Angelo. All rights reserved.
// Shared HTTP helpers for CLI subcommands that delegate to the daemon HTTP API.

use crate::cli_error::CliError;

fn auth_header_value(token: Option<&str>) -> Option<String> {
    token
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(|value| format!("Bearer {value}"))
}

fn with_auth(req: reqwest::RequestBuilder) -> reqwest::RequestBuilder {
    match auth_header_value(std::env::var("CONVERGIO_AUTH_TOKEN").ok().as_deref()) {
        Some(value) => req.header("Authorization", value),
        None => req,
    }
}

pub async fn fetch_and_print(url: &str, human: bool) -> Result<(), CliError> {
    let client = reqwest::Client::new();
    match with_auth(client.get(url)).send().await {
        Ok(resp) => {
            let status = resp.status();
            let val: serde_json::Value = resp
                .json()
                .await
                .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
            print_value(&val, human);
            if !status.is_success() {
                return Err(CliError::NotFound(val.to_string()));
            }
            Ok(())
        }
        Err(e) => Err(CliError::ApiCallFailed(format!(
            "error connecting to daemon: {e}"
        ))),
    }
}

pub async fn post_and_print(
    url: &str,
    body: &serde_json::Value,
    human: bool,
) -> Result<(), CliError> {
    let client = reqwest::Client::new();
    match with_auth(client.post(url)).json(body).send().await {
        Ok(resp) => {
            let status = resp.status();
            let val: serde_json::Value = resp
                .json()
                .await
                .map_err(|e| CliError::ApiCallFailed(format!("error parsing response: {e}")))?;
            print_value(&val, human);
            if !status.is_success() {
                return Err(CliError::NotFound(val.to_string()));
            }
            Ok(())
        }
        Err(e) => Err(CliError::ApiCallFailed(format!(
            "error connecting to daemon: {e}"
        ))),
    }
}

/// POST to `url` and return the parsed JSON value without printing.
/// Returns Err with an exit-code hint on failure (caller should exit).
pub async fn post_and_return(
    url: &str,
    body: &serde_json::Value,
) -> Result<serde_json::Value, i32> {
    let client = reqwest::Client::new();
    match with_auth(client.post(url)).json(body).send().await {
        Ok(resp) => {
            let status = resp.status();
            match resp.json::<serde_json::Value>().await {
                Ok(val) => {
                    if status.is_success() {
                        Ok(val)
                    } else {
                        eprintln!("error response from {url}: {val}");
                        Err(1)
                    }
                }
                Err(e) => {
                    eprintln!("error parsing response from {url}: {e}");
                    Err(2)
                }
            }
        }
        Err(e) => {
            eprintln!("error connecting to daemon ({url}): {e}");
            Err(2)
        }
    }
}

/// GET `url` and return the parsed JSON value without printing.
pub async fn get_and_return(url: &str) -> Result<serde_json::Value, i32> {
    let client = reqwest::Client::new();
    match with_auth(client.get(url)).send().await {
        Ok(resp) => {
            let status = resp.status();
            match resp.json::<serde_json::Value>().await {
                Ok(val) => {
                    if status.is_success() {
                        Ok(val)
                    } else {
                        eprintln!("error response from {url}: {val}");
                        Err(1)
                    }
                }
                Err(e) => {
                    eprintln!("error parsing response from {url}: {e}");
                    Err(2)
                }
            }
        }
        Err(e) => {
            eprintln!("error connecting to daemon ({url}): {e}");
            Err(2)
        }
    }
}

pub fn print_value(val: &serde_json::Value, human: bool) {
    if human {
        println!(
            "{}",
            serde_json::to_string_pretty(val).unwrap_or_else(|_| val.to_string())
        );
    } else {
        println!("{val}");
    }
}

#[cfg(test)]
mod tests {
    use super::auth_header_value;

    #[test]
    fn builds_bearer_header_when_token_present() {
        assert_eq!(
            auth_header_value(Some("secret")),
            Some("Bearer secret".to_string())
        );
    }

    #[test]
    fn skips_bearer_header_when_token_missing() {
        assert!(auth_header_value(None).is_none());
        assert!(auth_header_value(Some("   ")).is_none());
    }
}
