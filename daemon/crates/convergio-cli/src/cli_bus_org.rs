use serde_json::Value;

pub async fn run_org(api_url: &str, human: bool) {
    if !human {
        if let Err(e) =
            crate::cli_http::fetch_and_print(&format!("{api_url}/api/orgs"), false).await
        {
            eprintln!("error: {e}");
        }
        return;
    }
    match reqwest::get(format!("{api_url}/api/orgs")).await {
        Ok(resp) => match resp.json::<Value>().await {
            Ok(v) => println!("{}", render_org_tree(&v)),
            Err(e) => eprintln!("error: {e}"),
        },
        Err(e) => eprintln!("error: {e}"),
    }
}

pub fn render_org_tree(v: &Value) -> String {
    let orgs = v
        .get("orgs")
        .and_then(Value::as_array)
        .cloned()
        .or_else(|| v.as_array().cloned())
        .unwrap_or_default();
    if orgs.is_empty() {
        return "No orgs found.".to_string();
    }
    let mut out = Vec::new();
    for org in orgs {
        let name = org
            .get("id")
            .or_else(|| org.get("name"))
            .and_then(Value::as_str)
            .unwrap_or("unknown-org");
        let status = org
            .get("status")
            .and_then(Value::as_str)
            .unwrap_or("UNKNOWN");
        let budget = org
            .get("budget_pct")
            .or_else(|| org.get("budget_percent"))
            .and_then(Value::as_i64)
            .unwrap_or(0);
        out.push(format!("🏢 {name} [{status}] budget: {budget}%"));
        if let Some(ceo) = org.get("ceo") {
            out.push(format!(
                "  CEO: {} ({}, {})",
                ceo.get("name").and_then(Value::as_str).unwrap_or("n/a"),
                ceo.get("model")
                    .and_then(Value::as_str)
                    .unwrap_or("unknown"),
                ceo.get("status")
                    .and_then(Value::as_str)
                    .unwrap_or("unknown")
            ));
        }
        let departments = org
            .get("departments")
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default();
        for (i, d) in departments.iter().enumerate() {
            let dname = d.get("name").and_then(Value::as_str).unwrap_or("General");
            let dbranch = if i + 1 == departments.len() {
                "└──"
            } else {
                "├──"
            };
            out.push(format!("  {dbranch} {dname}"));
            let members = d
                .get("members")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();
            for (j, m) in members.iter().enumerate() {
                let mbranch = if i + 1 == departments.len() && j + 1 == members.len() {
                    "    └──"
                } else {
                    "    ├──"
                };
                out.push(format!(
                    "{mbranch} {} [{}] ({}, {})",
                    m.get("name").and_then(Value::as_str).unwrap_or("unknown"),
                    m.get("role").and_then(Value::as_str).unwrap_or("member"),
                    m.get("model").and_then(Value::as_str).unwrap_or("model"),
                    m.get("status").and_then(Value::as_str).unwrap_or("unknown")
                ));
            }
        }
    }
    out.join("\n")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn renders_tree_from_mock_json() {
        let data = serde_json::json!([{
            "id":"fitness-project","status":"ACTIVE","budget_pct":72,
            "ceo":{"name":"fitness-ceo","model":"sonnet","status":"active"},
            "departments":[
                {"name":"Engineering","members":[{"name":"dan","role":"lead","model":"claude","status":"active"},{"name":"rex","role":"reviewer","model":"copilot","status":"idle"}]},
                {"name":"Design","members":[{"name":"sara","role":"UX","model":"claude","status":"active"}]}
            ]
        }]);
        let out = render_org_tree(&data);
        assert!(out.contains("🏢 fitness-project [ACTIVE] budget: 72%"));
        assert!(out.contains("CEO: fitness-ceo"));
        assert!(out.contains("Engineering"));
        assert!(out.contains("dan [lead]"));
    }
}
