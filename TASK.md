# Fase 33: Telegram notification client

Repo: /Users/Roberdan/GitHub/convergio
Branch: agent/w-telegram (già creato nel worktree).

## Cosa fare
1. Crea daemon/crates/convergio-org/src/telegram.rs (max 250 righe):
   - pub struct TelegramClient { bot_token, chat_id }
   - pub async fn send(client, text) — POST https://api.telegram.org/bot<token>/sendMessage
   - pub fn format_notification(notif) — emoji per severity, nomi umani
   - Config: CONVERGIO_TELEGRAM_BOT_TOKEN e CONVERGIO_TELEGRAM_CHAT_ID da env
2. Aggiungi telegram a lib.rs
3. Aggiungi route POST /api/notify/telegram/test in routes.rs
4. cargo check --workspace && cargo test --workspace
5. commit, push, gh pr create --base main

Test: mock/unit solo, non chiamare API Telegram reale.