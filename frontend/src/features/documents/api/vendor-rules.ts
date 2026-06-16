import type {
  VendorRule,
  VendorRuleCreate,
  VendorRuleUpdate,
} from "../types/vendor-rule";
import { apiFetch, getApiErrorMessage } from "@/lib/api";

export async function listVendorRules(
  options: { signal?: AbortSignal } = {},
): Promise<VendorRule[]> {
  const response = await apiFetch("/vendor-rules", {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<VendorRule[]>;
}

export async function createVendorRule(
  payload: VendorRuleCreate,
): Promise<VendorRule> {
  const response = await apiFetch("/vendor-rules", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Create failed"));
  }

  return response.json() as Promise<VendorRule>;
}

export async function updateVendorRule(
  id: string,
  update: VendorRuleUpdate,
): Promise<VendorRule> {
  const response = await apiFetch(`/vendor-rules/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Update failed"));
  }

  return response.json() as Promise<VendorRule>;
}

export async function deleteVendorRule(id: string): Promise<void> {
  const response = await apiFetch(`/vendor-rules/${id}`, {
    method: "DELETE",
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(await getApiErrorMessage(response, "Delete failed"));
  }
}
