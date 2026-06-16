import type { SearchFilters, SearchResult } from "../types/search";
import { apiFetch, getApiErrorMessage } from "@/lib/api";

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
  const url = `/search${queryString ? `?${queryString}` : ""}`;

  const response = await apiFetch(url, {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getApiErrorMessage(response, "Search failed"));
  }

  return response.json() as Promise<SearchResult[]>;
}
