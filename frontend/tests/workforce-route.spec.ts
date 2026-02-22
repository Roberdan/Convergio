import { describe, it, expect } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const workforcePagePath = path.resolve(
  process.cwd(),
  "src/routes/(app)/workforce/+page.svelte",
);

describe("workforce page route", () => {
  it("creates the workforce page route file", () => {
    expect(existsSync(workforcePagePath)).toBe(true);
  });

  it("renders unified team table columns and action buttons", () => {
    const page = readFileSync(workforcePagePath, "utf-8");

    expect(page).toContain("Name");
    expect(page).toContain("Type");
    expect(page).toContain("Role");
    expect(page).toContain("Status");
    expect(page).toContain("Capabilities");

    expect(page).toContain("Invite Member");
    expect(page).toContain("Add Agent");
  });

  it("loads team members and invites with credentialed fetch calls", () => {
    const page = readFileSync(workforcePagePath, "utf-8");

    expect(page).toContain("/api/v1/teams/");
    expect(page).toContain("/api/v1/invites");
    expect(page).toContain("credentials: 'include'");
  });

  it("shows both human members and ai agents in one table", () => {
    const page = readFileSync(workforcePagePath, "utf-8");

    expect(page).toContain("human");
    expect(page).toContain("agent");
  });
});
