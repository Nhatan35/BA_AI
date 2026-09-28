export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

export type Role = "PROJECT_ADMIN" | "BA" | "BUSINESS_OWNER" | "MEDICAL_SME" | "TECH" | "QC" | "VIEWER";
export const roles: Role[] = ["PROJECT_ADMIN", "BA", "BUSINESS_OWNER", "MEDICAL_SME", "TECH", "QC", "VIEWER"];
export type Session = { user: {id: string; email: string; display_name: string}; csrf_token: string };
export type Project = {
  id: string; project_code: string; name: string; description: string; organization: string;
  scope: string; out_of_scope: string; status: string; my_role: Role; revision: number;
};
export type Member = {
  id: string; user_id: string; email: string; display_name: string; role: Role; status: string; revision: number;
};
export type Page<T> = { items: T[]; next_cursor: string | null };

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (options.method && !["GET", "HEAD"].includes(options.method) && path !== "/auth/login") {
    const session = await api<Session>("/auth/me");
    headers.set("X-CSRF-Token", session.csrf_token);
  }
  const response = await fetch(`/api/v1${path}`, { ...options, headers, credentials: "same-origin", cache: "no-store" });
  if (!response.ok) {
    const error = await response.json().catch(() => ({code: "UNAVAILABLE", message: "The service is unavailable."}));
    throw new ApiError(response.status, error.code, error.message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function message(error: unknown): string {
  return error instanceof Error ? error.message : "The operation could not be completed.";
}
