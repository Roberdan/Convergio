import { writable } from "svelte/store";

export interface AuthUser {
  id: string;
  email: string;
  [key: string]: unknown;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  initialized: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  loading: false,
  initialized: false,
  error: null,
};

export function hasSessionCookie(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie
    .split(";")
    .some((cookie) => cookie.trim().toLowerCase().startsWith("session="));
}

export function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>(initialState);

  async function fetchCurrentUser() {
    const response = await fetch("/api/v1/auth/me", {
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Unable to load current user");
    }

    const payload = await response.json();
    const user = (payload?.user ?? payload) as AuthUser;
    update((state) => ({
      ...state,
      user,
      isAuthenticated: true,
      error: null,
    }));
  }

  return {
    subscribe,
    async initialize() {
      if (typeof window === "undefined") return;

      update((state) => ({ ...state, loading: true }));
      try {
        if (!hasSessionCookie()) {
          set({ ...initialState, initialized: true });
          return;
        }

        await fetchCurrentUser();
      } catch (_error) {
        set({
          ...initialState,
          initialized: true,
          error: "Authentication session is invalid.",
        });
        return;
      } finally {
        update((state) => ({
          ...state,
          loading: false,
          initialized: true,
        }));
      }
    },
    async login(email: string, password: string) {
      update((state) => ({ ...state, loading: true, error: null }));

      try {
        const response = await fetch("/api/v1/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
          throw new Error("Invalid email or password");
        }

        await fetchCurrentUser();
      } catch (_error) {
        set({
          ...initialState,
          initialized: true,
          error: "Invalid email or password",
        });
        throw _error;
      } finally {
        update((state) => ({
          ...state,
          loading: false,
          initialized: true,
        }));
      }
    },
    async logout() {
      update((state) => ({ ...state, loading: true }));
      try {
        await fetch("/api/v1/auth/logout", {
          method: "POST",
          credentials: "include",
        });
      } finally {
        set({
          ...initialState,
          initialized: true,
        });
      }
    },
  };
}

export const authStore = createAuthStore();
