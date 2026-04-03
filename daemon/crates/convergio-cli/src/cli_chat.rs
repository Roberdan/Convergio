use crate::cli_error::CliError;
use std::io::{self, Write};

const RESET: &str = "\x1b[0m";
const BOLD: &str = "\x1b[1m";
const DIM: &str = "\x1b[2m";
const CYAN: &str = "\x1b[36m";
const GREEN: &str = "\x1b[32m";
const WHITE: &str = "\x1b[37m";
const BLUE: &str = "\x1b[34m";

const LOGO: &str = r#"
    ◆ ConvergioChat
"#;

pub async fn handle(api_url: &str, message: Option<String>) -> Result<(), CliError> {
    if let Some(msg) = message {
        // Single-shot mode: send message and print response
        let reply = send_message(api_url, &msg).await?;
        println!("{GREEN}{BOLD}Ali:{RESET} {reply}");
        return Ok(());
    }

    // Interactive REPL mode
    print_banner();

    loop {
        print!("{CYAN}{BOLD}you ▸{RESET} ");
        io::stdout().flush().unwrap();

        let mut input = String::new();
        if io::stdin().read_line(&mut input).is_err() || input.is_empty() {
            break;
        }

        let trimmed = input.trim();
        if trimmed.is_empty() { continue; }
        if trimmed == "/quit" || trimmed == "/exit" || trimmed == "/q" {
            println!("{DIM}Ciao!{RESET}");
            break;
        }
        if trimmed == "/help" {
            print_help();
            continue;
        }
        if trimmed == "/status" {
            if let Err(e) = crate::cli_status::handle(api_url).await {
                eprintln!("error: {e}");
            }
            continue;
        }

        // Send to Ali
        print!("{GREEN}{BOLD}Ali{RESET} {DIM}▸{RESET} ");
        io::stdout().flush().unwrap();

        match send_message(api_url, trimmed).await {
            Ok(reply) => println!("{WHITE}{reply}{RESET}"),
            Err(e) => println!("\x1b[31mError: {e}{RESET}"),
        }
        println!();
    }
    Ok(())
}

fn print_banner() {
    println!("{CYAN}{BOLD}{LOGO}{RESET}");
    println!("  {DIM}Chat with Ali orchestrator. Type /help for commands.{RESET}");
    println!("  {DIM}────────────────────────────────────────────────────{RESET}");
    println!();
}

fn print_help() {
    println!();
    println!("  {BOLD}Commands:{RESET}");
    println!("    {BLUE}/status{RESET}   Platform status overview");
    println!("    {BLUE}/help{RESET}     This message");
    println!("    {BLUE}/quit{RESET}     Exit chat");
    println!();
}

async fn send_message(api_url: &str, text: &str) -> Result<String, CliError> {
    let client = reqwest::Client::new();
    let body = serde_json::json!({
        "message": text,
        "agent": "ali",
    });
    let resp = client
        .post(format!("{api_url}/api/chat/message"))
        .json(&body)
        .send()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("send failed: {e}")))?;

    let json: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| CliError::ApiCallFailed(format!("parse failed: {e}")))?;

    Ok(json
        .get("reply")
        .or_else(|| json.get("message"))
        .and_then(|v| v.as_str())
        .unwrap_or("No response from Ali")
        .to_string())
}
