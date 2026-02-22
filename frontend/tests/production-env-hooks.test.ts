import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";

import { handleFetch } from "../src/hooks.server";

describe("production frontend configuration", () => {
  it("defines production API/BACKEND environment variables", () => {
    const envPath = resolve(process.cwd(), ".env.production");
    const envContent = readFileSync(envPath, "utf8");

    expect(envContent).toMatch(/API_URL=/);
    expect(envContent).toMatch(/BACKEND/i);
    expect(envContent).toContain("convergio.io");
  });
});

describe("hooks.server handleFetch", () => {
  it("forwards auth cookies to backend requests", async () => {
    const backendRequest = new Request("https://convergio-backend-prod.eastus.azurecontainerapps.io/api/v1/auth/me");
    const fetchSpy = vi.fn(async (request: Request) => new Response(request.headers.get("cookie") ?? "", { status: 200 }));

    const response = await handleFetch({
      event: {
        request: new Request("https://app.convergio.io/dashboard", {
          headers: { cookie: "auth_token=abc123; session=xyz" },
        }),
      } as never,
      request: backendRequest,
      fetch: fetchSpy,
    });

    expect(fetchSpy).toHaveBeenCalledOnce();
    expect(await response.text()).toContain("auth_token=abc123");
  });
});
