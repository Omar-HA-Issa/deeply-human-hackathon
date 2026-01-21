import { getJson, postJson } from "./client";

export type AuthUser = {
  id: number;
  username: string;
  email: string | null;
};

type AuthResponse = {
  user: AuthUser;
};

export function login(username: string, password: string) {
  return postJson<AuthResponse>("/api/auth/login", { username, password });
}

export function register(username: string, email: string, password: string) {
  return postJson<AuthResponse>("/api/auth/register", { username, email, password });
}

export function logout() {
  return postJson<Record<string, never>>("/api/auth/logout");
}

export function me() {
  return getJson<AuthResponse>("/api/auth/me");
}
