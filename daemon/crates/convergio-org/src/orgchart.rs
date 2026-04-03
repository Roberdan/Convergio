//! ASCII orgchart renderer — produces box-drawn and compact views.

use super::factory::OrgBlueprint;

/// Render a full boxed ASCII orgchart from a blueprint.
pub fn render_orgchart(blueprint: &OrgBlueprint) -> String {
    let w = 50;
    let hr = format!("├{}┤", "─".repeat(w));
    let top = format!("┌{}┐", "─".repeat(w));
    let bot = format!("└{}┘", "─".repeat(w));

    let mut lines: Vec<String> = Vec::new();
    lines.push(top);

    lines.push(pad_line(&format!("  Org: {}", blueprint.name), w));
    lines.push(pad_line(&format!("  Mission: {}", blueprint.mission), w));
    if let Some(b) = blueprint.budget_usd {
        let repo = blueprint.repo_path.as_deref().unwrap_or("—");
        lines.push(pad_line(&format!("  Budget: ${b} | Repo: {repo}"), w));
    }

    lines.push(hr.clone());

    lines.push(pad_line(
        &format!("  CEO: {} (coordinator)", blueprint.ceo_agent),
        w,
    ));
    let dept_count = blueprint.departments.len();
    for (i, dept) in blueprint.departments.iter().enumerate() {
        let is_last = i == dept_count - 1;
        let branch = if is_last { "└──" } else { "├──" };
        lines.push(pad_line(&format!("  {branch} {} Dept", dept.name), w));
        for agent in &dept.agents {
            let prefix = if is_last { "      " } else { "  │   " };
            let caps = agent.capabilities.join(",");
            let label = format!(
                "{prefix}└── {} ({}) [{caps}]",
                agent.name, agent.model,
            );
            lines.push(pad_line(&label, w));
        }
    }

    if !blueprint.night_agents.is_empty() {
        lines.push(hr.clone());
        lines.push(pad_line("  Night Agents (off-peak):", w));
        let na_count = blueprint.night_agents.len();
        for (i, na) in blueprint.night_agents.iter().enumerate() {
            let branch = if i == na_count - 1 { "└──" } else { "├──" };
            let label = format!("  {branch} {:18} {:5}  {}", na.name, na.time, na.schedule);
            lines.push(pad_line(&label, w));
        }
    }

    lines.push(hr);
    lines.push(pad_line("  Plan: (pending provisioning)", w));
    lines.push(bot);

    lines.join("\n")
}

/// Render a compact orgchart suitable for Telegram or narrow terminals.
pub fn render_orgchart_compact(blueprint: &OrgBlueprint) -> String {
    let mut lines: Vec<String> = Vec::new();

    lines.push(format!("Org: {}", blueprint.name));
    lines.push(format!("Mission: {}", blueprint.mission));
    lines.push(format!("CEO: {}", blueprint.ceo_agent));
    lines.push(String::new());

    for dept in &blueprint.departments {
        lines.push(format!("  {}", dept.name));
        for agent in &dept.agents {
            let caps = agent.capabilities.join(",");
            lines.push(format!("    {} ({}) [{}]", agent.name, agent.model, caps));
        }
    }

    if !blueprint.night_agents.is_empty() {
        lines.push(String::new());
        lines.push("Night:".into());
        for na in &blueprint.night_agents {
            lines.push(format!("  {} {} {}", na.name, na.time, na.schedule));
        }
    }

    lines.join("\n")
}

fn pad_line(text: &str, w: usize) -> String {
    let content = if text.len() > w { &text[..w] } else { text };
    format!("│{:<width$}│", content, width = w)
}
