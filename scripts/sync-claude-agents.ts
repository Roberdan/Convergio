#!/usr/bin/env tsx
/**
 * sync-claude-agents.ts
 * Generates .claude/agents/*.md from backend YAML/frontmatter definitions.
 * Single source of truth: backend/src/agents/definitions/*.md
 *
 * Usage: npx tsx scripts/sync-claude-agents.ts [--dry-run]
 */

import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync, unlinkSync } from "fs";
import { join, basename } from "path";

const DEFINITIONS_DIR = join(
  __dirname,
  "..",
  "backend",
  "src",
  "agents",
  "definitions"
);
const OUTPUT_DIR = join(__dirname, "..", ".claude", "agents");
const SKIP_FILES = ["CommonValuesAndPrinciples.md", "__init__.py", "agent.schema.json"];
const DRY_RUN = process.argv.includes("--dry-run");

interface AgentFrontmatter {
  name: string;
  description: string;
  tools: string[];
  color: string;
}

function parseFrontmatter(content: string): AgentFrontmatter | null {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const fm = match[1];
  const name = fm.match(/^name:\s*(.+)$/m)?.[1]?.trim() ?? "";
  const description = fm.match(/^description:\s*(.+)$/m)?.[1]?.trim() ?? "";
  const color = fm.match(/^color:\s*"?([^"\n]+)"?$/m)?.[1]?.trim() ?? "#666";

  let tools: string[] = [];
  const toolsMatch = fm.match(/^tools:\s*\[([^\]]*)\]/m);
  if (toolsMatch?.[1]) {
    tools = toolsMatch[1]
      .split(",")
      .map((t) => t.trim().replace(/"/g, ""))
      .filter(Boolean);
  }

  if (!name) return null;
  return { name, description, tools, color };
}

function extractCapabilities(body: string): string[] {
  const caps: string[] = [];
  const sections = [
    /## Core Competencies\n([\s\S]*?)(?=\n## |\n$)/,
    /## Core Identity\n([\s\S]*?)(?=\n## |\n$)/,
    /### .*?\n([\s\S]*?)(?=\n### |\n## |\n$)/,
  ];

  for (const pattern of sections) {
    const match = body.match(pattern);
    if (match) {
      const bullets = match[1].match(/^[-*]\s+\*\*(.+?)\*\*/gm);
      if (bullets) {
        for (const b of bullets.slice(0, 4)) {
          const text = b.replace(/^[-*]\s+\*\*/, "").replace(/\*\*.*/, "");
          caps.push(text);
        }
      }
      if (caps.length >= 3) break;
    }
  }

  return caps.length > 0 ? caps.slice(0, 5) : ["Specialist consultation", "Domain expertise"];
}

function inferModel(name: string, tools: string[]): string {
  const opusAgents = [
    "ali-chief-of-staff",
    "thor-quality-assurance-guardian",
    "satya-board-of-directors",
    "domik-mckinsey-strategic-decision-maker",
  ];
  if (opusAgents.includes(name)) return "opus";

  const haiku = ["coach-team-coach", "riccardo-storyteller", "jenny-inclusive-accessibility-champion"];
  if (haiku.includes(name)) return "haiku";

  if (tools.some((t) => ["Bash", "Edit", "Write", "Task"].includes(t))) return "sonnet";
  return "sonnet";
}

function mapTools(tools: string[]): string[] {
  const CLAUDE_TOOLS = ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"];
  const mapped = tools
    .filter((t) => CLAUDE_TOOLS.includes(t))
    .filter((v, i, a) => a.indexOf(v) === i);
  if (mapped.length === 0) return ["Read", "Grep", "Glob"];
  return mapped;
}

function generateAgentMd(fm: AgentFrontmatter, body: string): string {
  const model = inferModel(fm.name, fm.tools);
  const tools = mapTools(fm.tools);
  const caps = extractCapabilities(body);

  const humanName = fm.name
    .split("-")[0]
    .replace(/^\w/, (c) => c.toUpperCase());

  const role = fm.name.split("-").slice(1).join(" ").replace(/(^|\s)\w/g, (c) => c.toUpperCase());

  const lines: string[] = [
    "---",
    `name: ${fm.name}`,
    `description: ${fm.description}`,
    `model: ${model}`,
    `tools: [${tools.map((t) => `"${t}"`).join(", ")}]`,
    `color: "${fm.color}"`,
    "---",
    "",
    `# ${humanName} - ${role}`,
    "",
    fm.description,
    "",
    "## Capabilities",
    ...caps.map((c) => `- ${c}`),
    "",
    "## When to Use",
    `- Domain-specific tasks requiring ${role.toLowerCase()} expertise`,
    `- Cross-functional collaboration involving ${humanName}'s specialization`,
    "",
    "## Source",
    `Generated from \`backend/src/agents/definitions/${fm.name}.md\``,
    `Run \`npx tsx scripts/sync-claude-agents.ts\` to regenerate.`,
    "",
  ];

  return lines.join("\n");
}

function main(): void {
  if (!existsSync(DEFINITIONS_DIR)) {
    console.error(`Definitions directory not found: ${DEFINITIONS_DIR}`);
    process.exit(1);
  }

  if (!DRY_RUN) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const files = readdirSync(DEFINITIONS_DIR).filter(
    (f) => f.endsWith(".md") && !SKIP_FILES.includes(f)
  );

  // Collect existing agent files before writing so stale ones can be removed
  const existingAgentFiles = new Set<string>(
    existsSync(OUTPUT_DIR)
      ? readdirSync(OUTPUT_DIR).filter((f) => f.endsWith(".md"))
      : []
  );
  const writtenFiles = new Set<string>();

  let created = 0;
  let skipped = 0;

  for (const file of files) {
    const content = readFileSync(join(DEFINITIONS_DIR, file), "utf-8");
    const fm = parseFrontmatter(content);

    if (!fm) {
      console.warn(`SKIP ${file}: no valid frontmatter`);
      skipped++;
      continue;
    }

    const body = content.replace(/^---\n[\s\S]*?\n---\n/, "");
    const output = generateAgentMd(fm, body);
    const outFile = join(OUTPUT_DIR, `${fm.name}.md`);
    const outBasename = `${fm.name}.md`;

    if (DRY_RUN) {
      console.log(`DRY-RUN: would write ${basename(outFile)} (${output.length} bytes)`);
    } else {
      writeFileSync(outFile, output, "utf-8");
      console.log(`WRITE ${basename(outFile)}`);
    }
    writtenFiles.add(outBasename);
    created++;
  }

  // Remove stale agent files that no longer have a corresponding definition
  let removed = 0;
  for (const existing of existingAgentFiles) {
    if (!writtenFiles.has(existing)) {
      if (DRY_RUN) {
        console.log(`DRY-RUN: would remove stale ${existing}`);
      } else {
        unlinkSync(join(OUTPUT_DIR, existing));
        console.log(`REMOVE stale ${existing}`);
      }
      removed++;
    }
  }

  console.log(`\nDone: ${created} agents generated, ${skipped} skipped, ${removed} stale removed`);
}

main();
