import type {
  VendorRule,
  VendorRuleCreate,
  VendorRuleUpdate,
} from "../types/vendor-rule";

const apiBaseUrl = process.env
  .NEXT_PUBLIC_API_BASE_URL!.trim()
  .replace(/\/$/, "");

export async function listVendorRules(
  options: { signal?: AbortSignal } = {},
): Promise<VendorRule[]> {
  const response = await fetch(`${apiBaseUrl}/vendor-rules`, {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<VendorRule[]>;
}

export async function createVendorRule(
  payload: VendorRuleCreate,
): Promise<VendorRule> {
  const response = await fetch(`${apiBaseUrl}/vendor-rules`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Create failed"));
  }

  return response.json() as Promise<VendorRule>;
}

export async function updateVendorRule(
  id: string,
  update: VendorRuleUpdate,
): Promise<VendorRule> {
  const response = await fetch(`${apiBaseUrl}/vendor-rules/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Update failed"));
  }

  return response.json() as Promise<VendorRule>;
}

export async function deleteVendorRule(id: string): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/vendor-rules/${id}`, {
    method: "DELETE",
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(await getErrorMessage(response, "Delete failed"));
  }
}

async function getErrorMessage(response: Response, fallback: string) {
  try {
    const payload = (await response.json()) as { detail?: unknown };

    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall through to the generic status message.
  }

  return `${fallback} with status ${response.status}.`;
}
