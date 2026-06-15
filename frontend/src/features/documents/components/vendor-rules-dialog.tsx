"use client";

import { useEffect, useId, useMemo, useState, type ReactNode } from "react";
import { Button, Chip, Input, Surface, Typography } from "@heroui/react";
import {
  AlertCircle,
  ArrowRight,
  Check,
  Pencil,
  Plus,
  Search,
  Tag,
  Tags,
  Trash2,
  X,
} from "lucide-react";
import { CATEGORY_OPTIONS, categoryLabel } from "../lib/financial-display";
import {
  useVendorRules,
  type VendorRuleDraft,
} from "../hooks/use-vendor-rules";
import type { VendorRule } from "../types/vendor-rule";
import type { FinancialCategory } from "../types/financial-record";

const FIELD_CLASS =
  "min-h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600";

type VendorRulesDialogProps = {
  isOpen: boolean;
  onClose: () => void;
};

type VendorRulesPanelProps = {
  enabled?: boolean;
  className?: string;
};

export function VendorRulesPanel({
  enabled = true,
  className,
}: VendorRulesPanelProps) {
  const [query, setQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<
    FinancialCategory | "all"
  >("all");
  const vendorRules = useVendorRules(enabled);

  const {
    rules,
    isLoading,
    loadError,
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
  } = vendorRules;

  const filteredRules = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return rules.filter((rule) => {
      const matchesQuery =
        normalizedQuery.length === 0 ||
        [rule.keyword, rule.vendor, categoryLabel(rule.category)]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);
      const matchesCategory =
        categoryFilter === "all" || rule.category === categoryFilter;

      return matchesQuery && matchesCategory;
    });
  }, [categoryFilter, query, rules]);

  const categoryCount = new Set(rules.map((rule) => rule.category)).size;

  return (
    <Surface variant="transparent" className={className}>
      <Surface
        variant="transparent"
        className="grid gap-3 sm:grid-cols-3"
        aria-label="Vendor rule summary"
      >
        <VendorRulesMetric
          icon={<Tags className="size-4" aria-hidden />}
          label="Rules"
          value={rules.length}
        />
        <VendorRulesMetric
          icon={<Tag className="size-4" aria-hidden />}
          label="Categories"
          value={categoryCount}
        />
        <VendorRulesMetric
          icon={<Search className="size-4" aria-hidden />}
          label="In view"
          value={filteredRules.length}
        />
      </Surface>

      <Surface className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <Surface
          variant="transparent"
          className="border-b border-slate-200 px-4 py-4 sm:px-5"
        >
          <Surface
            variant="transparent"
            className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
          >
            <Surface variant="transparent">
              <Typography.Heading
                level={2}
                className="text-lg font-semibold text-slate-950"
              >
                Rule library
              </Typography.Heading>
              <Typography.Paragraph className="mt-1 text-sm text-slate-500">
                {rules.length === 1
                  ? "1 vendor rule"
                  : `${rules.length} vendor rules`}
              </Typography.Paragraph>
            </Surface>

            {isAdding && addDraft ? null : (
              <Button
                type="button"
                variant="primary"
                onPress={startAdd}
                isDisabled={editingId !== null}
                className="min-h-10 rounded-md bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 disabled:opacity-60"
              >
                <Plus className="size-4" aria-hidden />
                Add vendor
              </Button>
            )}
          </Surface>

          {isAdding && addDraft ? (
            <Surface variant="transparent" className="mt-4">
              <VendorRuleFormRow
                draft={addDraft}
                isBusy={isCreating}
                error={createError}
                submitLabel="Add vendor"
                busyLabel="Adding…"
                onChange={updateAddDraft}
                onSubmit={() => void createRule()}
                onCancel={cancelAdd}
              />
            </Surface>
          ) : null}

          <Surface
            variant="transparent"
            className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]"
          >
            <label className="relative block">
              <span className="sr-only">Search vendors</span>
              <Search
                className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400"
                aria-hidden
              />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search vendors or keywords"
                className="min-h-11 w-full rounded-md border border-slate-300 bg-white py-2 pl-10 pr-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
              />
            </label>

            <label className="block">
              <span className="sr-only">Filter vendors by category</span>
              <select
                value={categoryFilter}
                onChange={(event) =>
                  setCategoryFilter(
                    event.target.value as FinancialCategory | "all",
                  )
                }
                className="min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
              >
                <option value="all">All categories</option>
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </Surface>
        </Surface>

        <VendorRulesList
          rules={filteredRules}
          totalRules={rules.length}
          isLoading={isLoading}
          loadError={loadError}
          editingId={editingId}
          draft={draft}
          isSaving={isSaving}
          saveError={saveError}
          deletingId={deletingId}
          deleteError={deleteError}
          isAdding={isAdding}
          onStartAdd={startAdd}
          onStartEdit={startEdit}
          onCancelEdit={cancelEdit}
          onChangeDraft={updateDraft}
          onSaveEdit={() => void saveEdit()}
          onDelete={(id) => void removeRule(id)}
        />
      </Surface>
    </Surface>
  );
}

export function VendorRulesDialog({ isOpen, onClose }: VendorRulesDialogProps) {
  const headingId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <Surface
      variant="transparent"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 cursor-default bg-slate-950/40"
        onClick={onClose}
      />

      <Surface
        role="dialog"
        aria-modal="true"
        aria-labelledby={headingId}
        aria-describedby={descriptionId}
        className="relative flex max-h-[85vh] w-full max-w-2xl flex-col rounded-lg border border-slate-200 bg-white shadow-xl"
      >
        <Surface
          variant="transparent"
          className="flex items-start justify-between gap-4 border-b border-slate-200 p-6"
        >
          <Surface variant="transparent">
            <Typography.Heading
              level={2}
              id={headingId}
              className="text-lg font-semibold text-slate-950"
            >
              Vendors
            </Typography.Heading>
            <Typography.Paragraph
              id={descriptionId}
              className="mt-1 text-sm leading-6 text-slate-600"
            >
              Keywords the engine matches against a document to assign a vendor
              and category. Add your own or remove ones you don’t need.
            </Typography.Paragraph>
          </Surface>

          <Button
            type="button"
            variant="outline"
            onPress={onClose}
            className="min-h-9 shrink-0 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
          >
            Close
          </Button>
        </Surface>

        <Surface
          variant="transparent"
          className="min-h-0 flex-1 overflow-y-auto p-6"
        >
          <VendorRulesPanel enabled={isOpen} />
        </Surface>
      </Surface>
    </Surface>
  );
}

type VendorRulesListProps = {
  rules: VendorRule[];
  totalRules: number;
  isLoading: boolean;
  loadError: string | null;
  editingId: string | null;
  draft: VendorRuleDraft | null;
  isSaving: boolean;
  saveError: string | null;
  deletingId: string | null;
  deleteError: string | null;
  isAdding: boolean;
  onStartAdd: () => void;
  onStartEdit: (rule: VendorRule) => void;
  onCancelEdit: () => void;
  onChangeDraft: (patch: Partial<VendorRuleDraft>) => void;
  onSaveEdit: () => void;
  onDelete: (id: string) => void;
};

function VendorRulesMetric({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: number;
}) {
  return (
    <Surface className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <Surface variant="transparent" className="flex items-center gap-3">
        <Surface
          variant="transparent"
          className="grid size-9 place-items-center rounded-md bg-slate-100 text-slate-700"
        >
          {icon}
        </Surface>
        <Surface variant="transparent">
          <Typography.Paragraph className="text-2xl font-semibold text-slate-950">
            {value}
          </Typography.Paragraph>
          <Typography.Paragraph className="mt-0.5 text-sm text-slate-500">
            {label}
          </Typography.Paragraph>
        </Surface>
      </Surface>
    </Surface>
  );
}

function VendorRulesList({
  rules,
  totalRules,
  isLoading,
  loadError,
  editingId,
  draft,
  isSaving,
  saveError,
  deletingId,
  deleteError,
  isAdding,
  onStartAdd,
  onStartEdit,
  onCancelEdit,
  onChangeDraft,
  onSaveEdit,
  onDelete,
}: VendorRulesListProps) {
  if (isLoading) {
    return (
      <Surface variant="transparent" className="divide-y divide-slate-200">
        {Array.from({ length: 4 }).map((_, index) => (
          <Surface
            key={index}
            variant="transparent"
            className="flex min-h-24 items-center gap-4 px-4 py-4 sm:px-5"
          >
            <div className="size-10 shrink-0 animate-pulse rounded-md bg-slate-100" />
            <Surface variant="transparent" className="min-w-0 flex-1 space-y-2">
              <div className="h-4 w-2/5 animate-pulse rounded bg-slate-100" />
              <div className="h-3 w-1/4 animate-pulse rounded bg-slate-100" />
            </Surface>
          </Surface>
        ))}
      </Surface>
    );
  }

  if (loadError) {
    return (
      <Surface
        variant="transparent"
        className="flex items-start gap-3 px-4 py-5 text-rose-700 sm:px-5"
        role="alert"
      >
        <AlertCircle className="mt-0.5 size-5 shrink-0" aria-hidden />
        <Typography.Paragraph className="text-sm">
          {loadError}
        </Typography.Paragraph>
      </Surface>
    );
  }

  if (totalRules === 0) {
    return (
      <Surface
        variant="transparent"
        className="grid min-h-72 place-items-center px-4 py-10 text-center sm:px-5"
      >
        <Surface variant="transparent" className="max-w-sm">
          <Surface
            variant="transparent"
            className="mx-auto grid size-12 place-items-center rounded-lg bg-indigo-50 text-indigo-700"
          >
            <Tags className="size-5" aria-hidden />
          </Surface>
          <Typography.Heading
            level={3}
            className="mt-4 text-base font-semibold text-slate-950"
          >
            No vendors yet
          </Typography.Heading>
          <Typography.Paragraph className="mt-2 text-sm leading-6 text-slate-500">
            Add a vendor rule to start building the matching library.
          </Typography.Paragraph>
          <Button
            type="button"
            variant="primary"
            onPress={onStartAdd}
            className="mt-5 min-h-10 rounded-md bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
          >
            <Plus className="size-4" aria-hidden />
            Add vendor
          </Button>
        </Surface>
      </Surface>
    );
  }

  if (rules.length === 0) {
    return (
      <Surface variant="transparent" className="px-4 py-8 text-center sm:px-5">
        <Typography.Paragraph className="text-sm text-slate-500">
          No vendor rules match this view.
        </Typography.Paragraph>
      </Surface>
    );
  }

  return (
    <Surface variant="transparent">
      {deleteError ? (
        <Surface
          variant="transparent"
          role="alert"
          className="flex items-start gap-2 border-b border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700 sm:px-5"
        >
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
          <span>{deleteError}</span>
        </Surface>
      ) : null}

      <ul className="divide-y divide-slate-200">
        {rules.map((rule) => (
          <li key={rule.id}>
            {editingId === rule.id && draft ? (
              <Surface variant="transparent" className="px-4 py-4 sm:px-5">
                <VendorRuleFormRow
                  draft={draft}
                  isBusy={isSaving}
                  error={saveError}
                  submitLabel="Save"
                  busyLabel="Saving…"
                  onChange={onChangeDraft}
                  onSubmit={onSaveEdit}
                  onCancel={onCancelEdit}
                />
              </Surface>
            ) : (
              <VendorRuleRow
                rule={rule}
                isDeleting={deletingId === rule.id}
                isBusy={deletingId !== null || editingId !== null || isAdding}
                onEdit={onStartEdit}
                onDelete={onDelete}
              />
            )}
          </li>
        ))}
      </ul>
    </Surface>
  );
}

type VendorRuleRowProps = {
  rule: VendorRule;
  isDeleting: boolean;
  isBusy: boolean;
  onEdit: (rule: VendorRule) => void;
  onDelete: (id: string) => void;
};

function VendorRuleRow({
  rule,
  isDeleting,
  isBusy,
  onEdit,
  onDelete,
}: VendorRuleRowProps) {
  const [confirming, setConfirming] = useState(false);

  return (
    <Surface
      variant="transparent"
      className="flex flex-col gap-4 px-4 py-4 transition hover:bg-slate-50 sm:min-h-24 sm:flex-row sm:items-center sm:justify-between sm:px-5"
    >
      <Surface variant="transparent" className="flex min-w-0 items-start gap-3">
        <Surface
          variant="transparent"
          className="grid size-10 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600"
        >
          <Tag className="size-4" aria-hidden />
        </Surface>
        <Surface variant="transparent" className="min-w-0">
          <Surface
            variant="transparent"
            className="flex flex-wrap items-center gap-2 text-sm"
          >
            <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-xs font-semibold text-slate-700">
              {rule.keyword}
            </span>
            <ArrowRight className="size-4 text-slate-300" aria-hidden />
            <span className="truncate text-base font-semibold text-slate-950">
              {rule.vendor}
            </span>
          </Surface>
          <Typography.Paragraph className="mt-2 text-xs text-slate-500">
            Updated {formatRuleDate(rule.updated_at)}
          </Typography.Paragraph>
        </Surface>
      </Surface>

      <Surface
        variant="transparent"
        className="flex flex-wrap items-center gap-3 sm:shrink-0"
      >
        <Chip
          size="sm"
          variant="soft"
          className="rounded-md bg-indigo-50 text-xs font-semibold text-indigo-700"
        >
          {categoryLabel(rule.category)}
        </Chip>

        <Surface variant="transparent" className="flex shrink-0 gap-2">
          {confirming ? (
            <>
              <Button
                type="button"
                variant="primary"
                onPress={() => onDelete(rule.id)}
                isDisabled={isDeleting}
                className="min-h-9 rounded-md bg-rose-600 px-3 text-sm font-semibold text-white transition hover:bg-rose-700 focus:ring-2 focus:ring-rose-500 disabled:opacity-70"
              >
                <Check className="size-4" aria-hidden />
                {isDeleting ? "Deleting…" : "Confirm"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onPress={() => setConfirming(false)}
                isDisabled={isDeleting}
                className="min-h-9 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
              >
                <X className="size-4" aria-hidden />
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                onPress={() => onEdit(rule)}
                isDisabled={isBusy}
                className="min-h-9 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600 disabled:opacity-60"
              >
                <Pencil className="size-4" aria-hidden />
                Edit
              </Button>
              <Button
                type="button"
                variant="outline"
                onPress={() => setConfirming(true)}
                isDisabled={isBusy}
                className="min-h-9 rounded-md border border-slate-200 px-3 text-sm font-semibold text-rose-700 transition hover:bg-rose-50 focus:ring-2 focus:ring-rose-500 disabled:opacity-60"
              >
                <Trash2 className="size-4" aria-hidden />
                Delete
              </Button>
            </>
          )}
        </Surface>
      </Surface>
    </Surface>
  );
}

type VendorRuleFormRowProps = {
  draft: VendorRuleDraft;
  isBusy: boolean;
  error: string | null;
  submitLabel: string;
  busyLabel: string;
  onChange: (patch: Partial<VendorRuleDraft>) => void;
  onSubmit: () => void;
  onCancel: () => void;
};

function VendorRuleFormRow({
  draft,
  isBusy,
  error,
  submitLabel,
  busyLabel,
  onChange,
  onSubmit,
  onCancel,
}: VendorRuleFormRowProps) {
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
      className="space-y-3 rounded-md border border-indigo-200 bg-indigo-50/40 px-4 py-3"
    >
      <Surface
        variant="transparent"
        className="grid grid-cols-1 gap-3 sm:grid-cols-3"
      >
        <label className="block">
          <Typography.Paragraph className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
            Keyword
          </Typography.Paragraph>
          <Input
            value={draft.keyword}
            onChange={(event) => onChange({ keyword: event.target.value })}
            className={FIELD_CLASS}
            disabled={isBusy}
          />
        </label>

        <label className="block">
          <Typography.Paragraph className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
            Vendor
          </Typography.Paragraph>
          <Input
            value={draft.vendor}
            onChange={(event) => onChange({ vendor: event.target.value })}
            className={FIELD_CLASS}
            disabled={isBusy}
          />
        </label>

        <label className="block">
          <Typography.Paragraph className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
            Category
          </Typography.Paragraph>
          <select
            value={draft.category}
            onChange={(event) =>
              onChange({
                category: event.target.value as VendorRuleDraft["category"],
              })
            }
            className={FIELD_CLASS}
            disabled={isBusy}
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </Surface>

      {error ? (
        <Typography.Paragraph className="text-sm text-rose-700">
          {error}
        </Typography.Paragraph>
      ) : null}

      <Surface variant="transparent" className="flex gap-2">
        <Button
          type="submit"
          variant="primary"
          isDisabled={isBusy}
          className="min-h-9 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600 disabled:opacity-70"
        >
          <Check className="size-4" aria-hidden />
          {isBusy ? busyLabel : submitLabel}
        </Button>
        <Button
          type="button"
          variant="outline"
          onPress={onCancel}
          isDisabled={isBusy}
          className="min-h-9 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
        >
          <X className="size-4" aria-hidden />
          Cancel
        </Button>
      </Surface>
    </form>
  );
}

function formatRuleDate(value: string): string {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
