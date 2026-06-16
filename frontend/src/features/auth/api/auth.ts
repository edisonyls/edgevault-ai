import { apiFetch } from "@/lib/api";

export type WorkspaceKey = "owner" | "demo";

export type WorkspaceSession = {
  authenticated: boolean;
  workspace: {
    key: WorkspaceKey;
    display_name: string;
    read_only: boolean;
  } | null;
};

export async function getSession(
  options: { signal?: AbortSignal } = {},
): Promise<WorkspaceSession> {
  const response = await apiFetch("/auth/session", {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    return { authenticated: false, workspace: null };
  }

  return response.json() as Promise<WorkspaceSession>;
}

export async function login(
  workspace: WorkspaceKey,
  password: string,
): Promise<WorkspaceSession> {
  const response = await apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace, password }),
  });

  if (!response.ok) {
    throw new Error("Invalid workspace password.");
  }

  return response.json() as Promise<WorkspaceSession>;
}

export async function logout(): Promise<void> {
  await apiFetch("/auth/logout", { method: "POST" });
}
