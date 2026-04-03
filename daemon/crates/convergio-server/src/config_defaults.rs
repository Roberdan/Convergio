//! Default config.toml template — the first thing users see.

/// Commented TOML template written by `write_default_config`.
/// Every field shows its default so users know what to tweak.
pub const DEFAULT_CONFIG_TEMPLATE: &str = r#"# Convergio Daemon Configuration
# Docs: https://github.com/Roberdan/convergio
#
# All values below are defaults. Uncomment and edit to customize.
# An empty file is valid — every field has a sensible default.

[node]
# name = "my-machine"          # auto-detected from hostname if omitted
role = "standalone"             # standalone | coordinator | worker

[daemon]
port = 8420
auto_update = true
# quiet_hours = "23:00-07:00"  # suppresses non-critical notifications
# timezone = "Europe/Rome"     # IANA timezone for quiet_hours

[mesh]
transport = "lan"               # lan | tailscale | manual
discovery = "mdns"              # mdns | static | tailscale
# peers = ["192.168.1.10:8420"] # explicit peer addresses (static mode)

# [mesh.tailscale]
# enabled = false
# auth_key = ""                 # or set TAILSCALE_AUTH_KEY env var

[inference]
default_model = "claude-sonnet-4-6"
api_key_env = "ANTHROPIC_API_KEY"  # env var name holding the API key

[inference.fallback]
max_attempts = 3
t1 = ["local", "haiku", "sonnet"]
t2 = ["haiku", "local", "sonnet"]
t3 = ["sonnet", "opus"]
t4 = ["opus", "sonnet"]

[kernel]
model = "none"                  # "none" disables local kernel
# model_path = ""               # path to local model weights
# escalation_model = ""         # model used when kernel escalates
max_tokens = 2048

[telegram]
enabled = false
# token_keychain = ""           # macOS Keychain item name for bot token
"#;
