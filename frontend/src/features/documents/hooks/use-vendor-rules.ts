import { useCallback, useEffect, useState } from "react";
import type { FinancialCategory } from "../types/financial-record";
import type { VendorRule } from "../types/vendor-rule";
import {
  createVendorRule,
  deleteVendorRule,
  listVendorRules,
  updateVendorRule,
} from "../api/vendor-rules";

export type VendorRuleDraft = {
  keyword: string;
  vendor: string;
  category: FinancialCategory;
};

const EMPTY_DRAFT: VendorRuleDraft = {
  keyword: "",
  vendor: "",
  category: "other",
};

type UseVendorRules = {
  rules: VendorRule[];
  isLoading: boolean;
  loadError: string | null;
  reload: () => Promise<void>;
  isAdding: boolean;
  addDraft: VendorRuleDraft | null;
  isCreating: boolean;
  createError: string | null;
  startAdd: () => void;
  cancelAdd: () => void;
  updateAddDraft: (patch: Partial<VendorRuleDraft>) => void;
  createRule: () => Promise<void>;
  editingId: string | null;
  draft: VendorRuleDraft | null;
  isSaving: boolean;
  saveError: string | null;
  startEdit: (rule: VendorRule) => void;
  cancelEdit: () => void;
  updateDraft: (patch: Partial<VendorRuleDraft>) => void;
  saveEdit: () => Promise<void>;
  deletingId: string | null;
  deleteError: string | null;
  removeRule: (id: string) => Promise<void>;
};

// Loads the vendor rules and manages the add/edit/delete lifecycle. Pass
// `enabled` so the list only loads while the management dialog is open.
export function useVendorRules(enabled: boolean): UseVendorRules {
  const [rules, setRules] = useState<VendorRule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [isAdding, setIsAdding] = useState(false);
  const [addDraft, setAddDraft] = useState<VendorRuleDraft | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<VendorRuleDraft | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);

    try {
      const result = await listVendorRules();
      setRules(result);
    } catch (caught) {
      setLoadError(getErrorMessage(caught, "Could not load vendor rules."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const controller = new AbortController();

    async function load() {
      setIsLoading(true);
      setLoadError(null);

      try {
        const result = await listVendorRules({ signal: controller.signal });
        setRules(result);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }

        setLoadError(getErrorMessage(caught, "Could not load vendor rules."));
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => controller.abort();
  }, [enabled]);

  const startAdd = useCallback(() => {
    setCreateError(null);
    setAddDraft(EMPTY_DRAFT);
    setIsAdding(true);
  }, []);

  const cancelAdd = useCallback(() => {
    setIsAdding(false);
    setAddDraft(null);
    setCreateError(null);
  }, []);

  const updateAddDraft = useCallback((patch: Partial<VendorRuleDraft>) => {
    setAddDraft((current) => (current ? { ...current, ...patch } : current));
  }, []);

  const createRule = useCallback(async () => {
    if (!addDraft) {
      return;
    }

    const keyword = addDraft.keyword.trim();
    const vendor = addDraft.vendor.trim();

    if (!keyword || !vendor) {
      setCreateError("Keyword and vendor are both required.");
      return;
    }

    setIsCreating(true);
    setCreateError(null);

    try {
      const created = await createVendorRule({
        keyword,
        vendor,
        category: addDraft.category,
      });
      setRules((current) => [created, ...current]);
      setIsAdding(false);
      setAddDraft(null);
    } catch (caught) {
      setCreateError(getErrorMessage(caught, "Could not add the vendor."));
    } finally {
      setIsCreating(false);
    }
  }, [addDraft]);

  const startEdit = useCallback((rule: VendorRule) => {
    setEditingId(rule.id);
    setSaveError(null);
    setDeleteError(null);
    setDraft({
      keyword: rule.keyword,
      vendor: rule.vendor,
      category: rule.category,
    });
  }, []);

  const cancelEdit = useCallback(() => {
    setEditingId(null);
    setDraft(null);
    setSaveError(null);
  }, []);

  const updateDraft = useCallback((patch: Partial<VendorRuleDraft>) => {
    setDraft((current) => (current ? { ...current, ...patch } : current));
  }, []);

  const saveEdit = useCallback(async () => {
    if (!editingId || !draft) {
      return;
    }

    const keyword = draft.keyword.trim();
    const vendor = draft.vendor.trim();

    if (!keyword || !vendor) {
      setSaveError("Keyword and vendor are both required.");
      return;
    }

    setIsSaving(true);
    setSaveError(null);

    try {
      const updated = await updateVendorRule(editingId, {
        keyword,
        vendor,
        category: draft.category,
      });
      setRules((current) =>
        current.map((rule) => (rule.id === updated.id ? updated : rule)),
      );
      setEditingId(null);
      setDraft(null);
    } catch (caught) {
      setSaveError(getErrorMessage(caught, "Could not save changes."));
    } finally {
      setIsSaving(false);
    }
  }, [editingId, draft]);

  const removeRule = useCallback(
    async (id: string) => {
      setDeletingId(id);
      setDeleteError(null);

      try {
        await deleteVendorRule(id);
        setRules((current) => current.filter((rule) => rule.id !== id));

        if (editingId === id) {
          setEditingId(null);
          setDraft(null);
        }
      } catch (caught) {
        setDeleteError(getErrorMessage(caught, "Could not delete the rule."));
      } finally {
        setDeletingId(null);
      }
    },
    [editingId],
  );

  return {
    rules,
    isLoading,
    loadError,
    reload,
    isAdding,
    addDraft,
    isCreating,
    createError,
    startAdd,
    cancelAdd,
    updateAddDraft,
    createRule,
    editingId,
    draft,
    isSaving,
    saveError,
    startEdit,
    cancelEdit,
    updateDraft,
    saveEdit,
    deletingId,
    deleteError,
    removeRule,
  };
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return fallback;
}
