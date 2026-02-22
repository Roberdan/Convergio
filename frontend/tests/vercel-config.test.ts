import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("Vercel deployment configuration", () => {
  it("uses adapter-vercel with nodejs20.x runtime and fra1 region in svelte config", () => {
    const configPath = resolve(process.cwd(), "svelte.config.js");
    const configSource = readFileSync(configPath, "utf8");

    expect(configSource).toContain("@sveltejs/adapter-vercel");
    expect(configSource).toContain('runtime: "nodejs20.x"');
    expect(configSource).toContain('regions: ["fra1"]');
  });

  it("defines fra1 region, build command, and required cron jobs in vercel.json", () => {
    const vercelPath = resolve(process.cwd(), "vercel.json");
    const vercelConfig = JSON.parse(readFileSync(vercelPath, "utf8"));

    expect(vercelConfig.regions).toContain("fra1");
    expect(vercelConfig.buildCommand).toBeDefined();

    const jobs = (vercelConfig.crons ?? []) as Array<{
      path: string;
      schedule: string;
    }>;
    expect(jobs).toEqual(
      expect.arrayContaining([
        { path: "/api/cron/data-retention", schedule: "0 2 * * *" },
        { path: "/api/cron/metrics-push", schedule: "*/5 * * * *" },
      ]),
    );
  });
});
