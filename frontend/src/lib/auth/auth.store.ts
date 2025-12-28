import { writable } from "svelte/store";
import type { AuthState } from "./auth.types";

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  loading: false,
  error: null,
};

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>(initialState);

  return {
    subscribe,
    setAuth: (token: string, user: any) => {
      update((state) => ({
        ...state,
        token,
        user,
        isAuthenticated: true,
        error: null,
      }));
    },
    clearAuth: () => {
      set(initialState);
    },
    logout: () => {
      set(initialState);
    },
    setLoading: (loading: boolean) => {
      update((state) => ({ ...state, loading }));
    },
    setError: (error: string | null) => {
      update((state) => ({ ...state, error }));
    },
  };
}

export const authStore = createAuthStore();
