import { useCallback, useEffect, useState } from "react";
import { searchDocuments } from "../api/search";
import {
  EMPTY_SEARCH_FILTERS,
  type SearchFilters,
  type SearchResult,
} from "../types/search";

const DEBOUNCE_MS = 300;

type UseSearch = {
  filters: SearchFilters;
  results: SearchResult[];
  isLoading: boolean;
  error: string | null;
  setFilters: (patch: Partial<SearchFilters>) => void;
  clearFilters: () => void;
};

export function useSearch(): UseSearch {
  const [filters, setFiltersState] =
    useState<SearchFilters>(EMPTY_SEARCH_FILTERS);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const timer = setTimeout(async () => {
      try {
        setIsLoading(true);
        setError(null);
        setResults(
          await searchDocuments(filters, { signal: controller.signal }),
        );
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }

        setError(getErrorMessage(caught, "Could not run search."));
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }, DEBOUNCE_MS);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [filters]);

  const setFilters = useCallback((patch: Partial<SearchFilters>) => {
    setFiltersState((current) => ({ ...current, ...patch }));
  }, []);

  const clearFilters = useCallback(() => {
    setFiltersState(EMPTY_SEARCH_FILTERS);
  }, []);

  return { filters, results, isLoading, error, setFilters, clearFilters };
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
}
