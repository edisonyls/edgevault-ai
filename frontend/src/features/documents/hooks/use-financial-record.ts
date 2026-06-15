import { useCallback, useEffect, useState } from "react";
import {
  type FinancialCategory,
  type FinancialDocumentType,
  type FinancialRecord,
  type FinancialRecordUpdate,
  type PaymentStatus,
  getFinancialRecord,
  updateFinancialRecord,
} from "../api/financial-records";

export type FinancialRecordDraft = {
  vendor: string;
  documentType: FinancialDocumentType;
  category: FinancialCategory;
  paymentStatus: PaymentStatus;
  totalAmount: string;
  currency: string;
  transactionDate: string;
  dueDate: string;
};

type UseFinancialRecord = {
  record: FinancialRecord | null;
  isLoading: boolean;
  loadError: string | null;
  isEditing: boolean;
  isSaving: boolean;
  saveError: string | null;
  draft: FinancialRecordDraft | null;
  startEdit: () => void;
  cancelEdit: () => void;
  updateDraft: (patch: Partial<FinancialRecordDraft>) => void;
  save: () => Promise<void>;
};

function toDraft(record: FinancialRecord): FinancialRecordDraft {
  return {
    vendor: record.vendor ?? "",
    documentType: record.document_type ?? "other",
    category: record.category ?? "other",
    paymentStatus: record.payment_status ?? "unknown",
    totalAmount:
      record.total_amount === null ? "" : String(record.total_amount),
    currency: record.currency,
    transactionDate: record.transaction_date ?? "",
    dueDate: record.due_date ?? "",
  };
}

// Loads the structured financial record for a single document and manages the
// manual-correction edit lifecycle.
export function useFinancialRecord(
  uploadId: string | null,
  onSaved?: () => void,
): UseFinancialRecord {
  const [record, setRecord] = useState<FinancialRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [draft, setDraft] = useState<FinancialRecordDraft | null>(null);

  useEffect(() => {
    if (!uploadId) {
      return;
    }

    const id = uploadId;
    const controller = new AbortController();

    async function load() {
      setRecord(null);
      setIsEditing(false);
      setSaveError(null);
      setDraft(null);
      setIsLoading(true);
      setLoadError(null);

      try {
        const result = await getFinancialRecord(id, {
          signal: controller.signal,
        });
        setRecord(result);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }

        setLoadError(getErrorMessage(caught, "Could not load extracted data."));
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => controller.abort();
  }, [uploadId]);

  const startEdit = useCallback(() => {
    if (!record) {
      return;
    }

    setDraft(toDraft(record));
    setSaveError(null);
    setIsEditing(true);
  }, [record]);

  const cancelEdit = useCallback(() => {
    setIsEditing(false);
    setSaveError(null);
    setDraft(null);
  }, []);

  const updateDraft = useCallback((patch: Partial<FinancialRecordDraft>) => {
    setDraft((current) => (current ? { ...current, ...patch } : current));
  }, []);

  const save = useCallback(async () => {
    if (!record || !draft) {
      return;
    }

    const update = buildUpdate(draft);

    if (update instanceof Error) {
      setSaveError(update.message);
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      const updated = await updateFinancialRecord(record.id, update);
      setRecord(updated);
      setIsEditing(false);
      setDraft(null);
      onSaved?.();
    } catch (caught) {
      setSaveError(getErrorMessage(caught, "Could not save changes."));
    } finally {
      setIsSaving(false);
    }
  }, [record, draft, onSaved]);

  return {
    record,
    isLoading,
    loadError,
    isEditing,
    isSaving,
    saveError,
    draft,
    startEdit,
    cancelEdit,
    updateDraft,
    save,
  };
}

function buildUpdate(
  draft: FinancialRecordDraft,
): FinancialRecordUpdate | Error {
  let totalAmount: number | null = null;
  const trimmedAmount = draft.totalAmount.trim();

  if (trimmedAmount.length > 0) {
    const parsed = Number(trimmedAmount);

    if (!Number.isFinite(parsed) || parsed < 0) {
      return new Error("Total amount must be a number of 0 or more.");
    }

    totalAmount = Math.round(parsed * 100) / 100;
  }

  const currency = draft.currency.trim();

  if (currency.length === 0) {
    return new Error("Currency is required.");
  }

  return {
    vendor: draft.vendor.trim() || null,
    document_type: draft.documentType,
    category: draft.category,
    payment_status: draft.paymentStatus,
    total_amount: totalAmount,
    currency,
    transaction_date: draft.transactionDate || null,
    due_date: draft.dueDate || null,
  };
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
}
