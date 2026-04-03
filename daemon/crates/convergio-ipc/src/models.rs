use rusqlite::params;

use crate::types::{IpcError, IpcResult, ModelEntry, NodeCapabilities, Subscription};
use convergio_db::pool::ConnPool;

// ── Model registry ───────────────────────────────

pub fn store_models(
    pool: &ConnPool,
    host: &str,
    provider: &str,
    models: &[(String, f64, String)],
) -> IpcResult<()> {
    let conn = pool.get()?;
    for (name, size_gb, quant) in models {
        conn.execute(
            "INSERT OR REPLACE INTO ipc_model_registry
             (host, provider, model, size_gb, quantization, last_seen)
             VALUES (?1, ?2, ?3, ?4, ?5, strftime('%Y-%m-%dT%H:%M:%f','now'))",
            params![host, provider, name, size_gb, quant],
        )?;
    }
    Ok(())
}

pub fn get_all_models(pool: &ConnPool) -> IpcResult<Vec<ModelEntry>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT host, provider, model, size_gb, quantization, last_seen
         FROM ipc_model_registry ORDER BY host, provider, model",
    )?;
    let models = stmt
        .query_map([], |row| {
            Ok(ModelEntry {
                host: row.get(0)?,
                provider: row.get(1)?,
                model: row.get(2)?,
                size_gb: row.get(3)?,
                quantization: row.get(4)?,
                last_seen: row.get(5)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(models)
}

// ── Node capabilities ────────────────────────────

pub fn advertise_capabilities(pool: &ConnPool, host: &str) -> IpcResult<()> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT provider, GROUP_CONCAT(model)
         FROM ipc_model_registry WHERE host = ?1 GROUP BY provider",
    )?;
    let providers: Vec<(String, String)> = stmt
        .query_map(params![host], |row| Ok((row.get(0)?, row.get(1)?)))?
        .filter_map(|r| r.ok())
        .collect();
    for (provider, models_csv) in &providers {
        let models: Vec<&str> = models_csv.split(',').collect();
        let json = serde_json::to_string(&models).unwrap_or_else(|_| "[]".to_string());
        conn.execute(
            "INSERT OR REPLACE INTO ipc_node_capabilities (host, provider, models, updated_at)
             VALUES (?1, ?2, ?3, strftime('%Y-%m-%dT%H:%M:%f','now'))",
            params![host, provider, json],
        )?;
    }
    Ok(())
}

pub fn get_all_capabilities(pool: &ConnPool) -> IpcResult<Vec<NodeCapabilities>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT host, provider, models, updated_at
         FROM ipc_node_capabilities ORDER BY host",
    )?;
    let caps = stmt
        .query_map([], |row| {
            Ok(NodeCapabilities {
                host: row.get(0)?,
                provider: row.get(1)?,
                models: serde_json::from_str::<Vec<String>>(&row.get::<_, String>(2)?)
                    .unwrap_or_default(),
                updated_at: row.get(3)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(caps)
}

// ── Subscriptions ────────────────────────────────

pub fn add_subscription(pool: &ConnPool, sub: &Subscription) -> IpcResult<()> {
    let conn = pool.get()?;
    let models_json = serde_json::to_string(&sub.models).unwrap_or_else(|_| "[]".to_string());
    conn.execute(
        "INSERT OR REPLACE INTO ipc_subscriptions
         (name, provider, plan, budget_usd, reset_day, models)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![sub.name, sub.provider, sub.plan, sub.budget_usd, sub.reset_day, models_json],
    )?;
    Ok(())
}

pub fn list_subscriptions(pool: &ConnPool) -> IpcResult<Vec<Subscription>> {
    let conn = pool.get()?;
    let mut stmt = conn.prepare(
        "SELECT name, provider, plan, budget_usd, reset_day, models
         FROM ipc_subscriptions ORDER BY name",
    )?;
    let subs = stmt
        .query_map([], |row| {
            Ok(Subscription {
                name: row.get(0)?,
                provider: row.get(1)?,
                plan: row.get(2)?,
                budget_usd: row.get(3)?,
                reset_day: row.get(4)?,
                models: serde_json::from_str::<Vec<String>>(&row.get::<_, String>(5)?)
                    .unwrap_or_default(),
            })
        })?
        .filter_map(|r| r.ok())
        .collect();
    Ok(subs)
}

pub fn remove_subscription(pool: &ConnPool, name: &str) -> IpcResult<bool> {
    let conn = pool.get()?;
    let deleted = conn.execute(
        "DELETE FROM ipc_subscriptions WHERE name = ?1",
        params![name],
    )?;
    if deleted == 0 {
        return Err(IpcError::NotFound(format!("subscription '{name}'")));
    }
    Ok(true)
}

// ── Provider probing (async) ─────────────────────

pub async fn probe_ollama() -> Result<Vec<(String, f64, String)>, IpcError> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| IpcError::Http(format!("client: {e}")))?;
    let resp = client
        .get("http://localhost:11434/api/tags")
        .send()
        .await
        .map_err(|e| IpcError::Http(format!("ollama: {e}")))?;
    let body: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| IpcError::Http(format!("parse: {e}")))?;
    let models = body["models"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .map(|m| {
                    let name = m["name"].as_str().unwrap_or("unknown").to_string();
                    let size = m["size"].as_u64().unwrap_or(0) as f64 / 1_073_741_824.0;
                    let quant = m["details"]["quantization_level"]
                        .as_str()
                        .unwrap_or("")
                        .to_string();
                    (name, size, quant)
                })
                .collect()
        })
        .unwrap_or_default();
    Ok(models)
}

pub async fn probe_lmstudio() -> Result<Vec<(String, f64, String)>, IpcError> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| IpcError::Http(format!("client: {e}")))?;
    let resp = client
        .get("http://localhost:1234/v1/models")
        .send()
        .await
        .map_err(|e| IpcError::Http(format!("lmstudio: {e}")))?;
    let body: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| IpcError::Http(format!("parse: {e}")))?;
    let models = body["data"]
        .as_array()
        .map(|arr| {
            arr.iter()
                .map(|m| {
                    let name = m["id"].as_str().unwrap_or("unknown").to_string();
                    (name, 0.0, String::new())
                })
                .collect()
        })
        .unwrap_or_default();
    Ok(models)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pool() -> ConnPool {
        let p = convergio_db::pool::create_memory_pool().unwrap();
        let conn = p.get().unwrap();
        convergio_db::migration::ensure_registry(&conn).unwrap();
        convergio_db::migration::apply_migrations(&conn, "ipc", &crate::schema::migrations())
            .unwrap();
        p
    }

    #[test]
    fn store_and_list_models() {
        let p = pool();
        let models = vec![
            ("qwen2.5:7b".to_string(), 4.5, "Q4_K_M".to_string()),
            ("llama3:8b".to_string(), 5.0, "Q5_K_S".to_string()),
        ];
        store_models(&p, "m5max", "ollama", &models).unwrap();
        let all = get_all_models(&p).unwrap();
        assert_eq!(all.len(), 2);
    }

    #[test]
    fn subscription_crud() {
        let p = pool();
        let sub = Subscription {
            name: "anthropic-pro".into(),
            provider: "anthropic".into(),
            plan: "pro".into(),
            budget_usd: 100.0,
            reset_day: 15,
            models: vec!["claude-opus".into()],
        };
        add_subscription(&p, &sub).unwrap();
        let subs = list_subscriptions(&p).unwrap();
        assert_eq!(subs.len(), 1);
        assert_eq!(subs[0].models, vec!["claude-opus"]);
        remove_subscription(&p, "anthropic-pro").unwrap();
        assert_eq!(list_subscriptions(&p).unwrap().len(), 0);
    }

    #[test]
    fn capabilities_advertised() {
        let p = pool();
        let models = vec![("m1".to_string(), 1.0, "Q4".to_string())];
        store_models(&p, "m5max", "ollama", &models).unwrap();
        advertise_capabilities(&p, "m5max").unwrap();
        let caps = get_all_capabilities(&p).unwrap();
        assert_eq!(caps.len(), 1);
        assert_eq!(caps[0].host, "m5max");
    }
}
