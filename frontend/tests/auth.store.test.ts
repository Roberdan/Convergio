import { beforeEach, describe, expect, it, vi } from "vitest";
import { get } from "svelte/store";
import { createAuthStore, hasSessionCookie } from "$lib/stores/auth";

describe("auth store", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    Object.defineProperty(document, "cookie", {
      value: "",
      writable: true,
      configurable: true,
    });
  });

  it("detects session cookie", () => {
    Object.defineProperty(document, "cookie", {
      value: "foo=bar; session=abc123",
      writable: true,
      configurable: true,
    });

    expect(hasSessionCookie()).toBe(true);
  });

  it("initializes unauthenticated state without session cookie", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const auth = createAuthStore();

    await auth.initialize();

    const state = get(auth);
    expect(state.initialized).toBe(true);
    expect(state.isAuthenticated).toBe(false);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("loads current user when session cookie exists", async () => {
    Object.defineProperty(document, "cookie", {
      value: "session=abc123",
      writable: true,
      configurable: true,
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ user: { id: "u1", email: "a@b.com" } }),
      }),
    );
    const auth = createAuthStore();

    await auth.initialize();

    const state = get(auth);
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.email).toBe("a@b.com");
    expect(fetch).toHaveBeenCalledWith("/api/v1/auth/me", {
      credentials: "include",
    });
  });

  it("logs in with credentials included", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ user: { id: "u1", email: "new@user.com" } }),
        }),
    );
    const auth = createAuthStore();

    await auth.login("new@user.com", "password123");

    const state = get(auth);
    expect(state.isAuthenticated).toBe(true);
    expect(state.user?.email).toBe("new@user.com");
    expect(fetch).toHaveBeenNthCalledWith(1, "/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        email: "new@user.com",
        password: "password123",
      }),
    });
  });
});
