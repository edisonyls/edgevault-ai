import type { SearchFilters, SearchResult } from "../types/search";

const apiBaseUrl = process.env
  .NEXT_PUBLIC_API_BASE_URL!.trim()
  .replace(/\/$/, "");

export async function searchDocuments(
  filters: SearchFilters,
  options: { signal?: AbortSignal } = {},
): Promise<SearchResult[]> {
  const query = new URLSearchParams();

  const q = filters.q.trim();
  if (q) {
    query.set("q", q);
  }
  if (filters.mode !== "keyword") {
    query.set("mode", filters.mode);
  }
  if (filters.category !== "all") {
    query.set("category", filters.category);
  }
  if (filters.documentType !== "all") {
    query.set("document_type", filters.documentType);
  }
  const vendor = filters.vendor.trim();
  if (vendor) {
    query.set("vendor", vendor);
  }
  if (filters.from) {
    query.set("from", filters.from);
  }
  if (filters.to) {
    query.set("to", filters.to);
  }

  const queryString = query.toString();
  const url = `${apiBaseUrl}/search${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Search failed"));
  }

  return response.json() as Promise<SearchResult[]>;
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
