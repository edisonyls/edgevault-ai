import type {
  FinancialRecord,
  FinancialRecordUpdate,
} from "../types/financial-record";
import { apiFetch, getApiErrorMessage } from "@/lib/api";

export async function listFinancialRecords(
  options: { signal?: AbortSignal; limit?: number } = {},
): Promise<FinancialRecord[]> {
  const query = new URLSearchParams();
  if (options.limit !== undefined) {
    query.set("limit", String(options.limit));
  }

  const queryString = query.toString();
  const url = `/financial-records${queryString ? `?${queryString}` : ""}`;

  const response = await apiFetch(url, {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<FinancialRecord[]>;
}

/**
 * Fetches the structured record for one document. Returns null when extraction
 * has not produced a record yet.
 */
export async function getFinancialRecord(
  uploadId: string,
  options: { signal?: AbortSignal } = {},
): Promise<FinancialRecord | null> {
  const response = await apiFetch(`/uploads/${uploadId}/financial-record`, {
    method: "GET",
    signal: options.signal,
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<FinancialRecord>;
}

export async function updateFinancialRecord(
  id: string,
  update: FinancialRecordUpdate,
): Promise<FinancialRecord> {
  const response = await apiFetch(`/financial-records/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Update failed"));
  }

  return response.json() as Promise<FinancialRecord>;
}
