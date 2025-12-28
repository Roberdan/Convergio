export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
  avatar?: string;
}

export interface AuthResponse {
  token: string;
  user: User;
  expiresAt?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}
