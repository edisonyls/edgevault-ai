import { useCallback, useEffect, useMemo, useState } from "react";
import { listFinancialRecords } from "@/features/documents/api/financial-records";
import type { FinancialRecord } from "@/features/documents/types/financial-record";
import {
  computeDashboardAnalytics,
  type DashboardAnalytics,
} from "../lib/analytics";

// The list endpoint caps at 500 records, which comfortably covers a personal
// vault and keeps every chart computed from a single request.
const RECORD_LIMIT = 500;

type UseDashboard = {
  analytics: DashboardAnalytics;
  isLoading: boolean;
  error: string | null;
  reload: () => Promise<void>;
};

export function useDashboard(): UseDashboard {
  const [records, setRecords] = useState<FinancialRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await listFinancialRecords({ limit: RECORD_LIMIT });
      setRecords(result);
    } catch (caught) {
      setError(getErrorMessage(caught, "Could not load your spending data."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const result = await listFinancialRecords({
          limit: RECORD_LIMIT,
          signal: controller.signal,
        });
        setRecords(result);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }

        setError(getErrorMessage(caught, "Could not load your spending data."));
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => controller.abort();
  }, []);

  const analytics = useMemo(
    () => computeDashboardAnalytics(records),
    [records],
  );

  return { analytics, isLoading, error, reload };
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
}
