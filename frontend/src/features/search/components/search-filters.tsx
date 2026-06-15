"use client";

import { Button, Input, Surface, Typography } from "@heroui/react";
import { Search, X } from "lucide-react";
import {
  CATEGORY_OPTIONS,
  DOCUMENT_TYPE_OPTIONS,
} from "@/features/documents/lib/financial-display";
import type { SearchFilters } from "../types/search";

const FIELD_CLASS =
  "min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-700 outline-none transition focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600";

type SearchFiltersBarProps = {
  filters: SearchFilters;
  hasActiveFilters: boolean;
  onChange: (patch: Partial<SearchFilters>) => void;
  onClear: () => void;
};

export function SearchFiltersBar({
  filters,
  hasActiveFilters,
  onChange,
  onClear,
}: SearchFiltersBarProps) {
  return (
    <Surface className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <label className="relative block">
        <span className="sr-only">Search documents</span>
        <Search
          className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400"
          aria-hidden
        />
        <Input
          value={filters.q}
          onChange={(event) => onChange({ q: event.target.value })}
          placeholder="Search document text, e.g. electricity, Coles…"
          className="min-h-12 w-full rounded-md border border-slate-300 bg-white py-2 pl-10 pr-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
        />
      </label>

      <Surface
        variant="transparent"
        className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
      >
        <FilterField label="Category">
          <select
            value={filters.category}
            onChange={(event) =>
              onChange({
                category: event.target.value as SearchFilters["category"],
              })
            }
            className={FIELD_CLASS}
          >
            <option value="all">All categories</option>
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </FilterField>

        <FilterField label="Type">
          <select
            value={filters.documentType}
            onChange={(event) =>
              onChange({
                documentType: event.target
                  .value as SearchFilters["documentType"],
              })
            }
            className={FIELD_CLASS}
          >
            <option value="all">All types</option>
            {DOCUMENT_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </FilterField>

        <FilterField label="From">
          <input
            type="date"
            value={filters.from}
            max={filters.to || undefined}
            onChange={(event) => onChange({ from: event.target.value })}
            className={FIELD_CLASS}
          />
        </FilterField>

        <FilterField label="To">
          <input
            type="date"
            value={filters.to}
            min={filters.from || undefined}
            onChange={(event) => onChange({ to: event.target.value })}
            className={FIELD_CLASS}
          />
        </FilterField>
      </Surface>

      {hasActiveFilters ? (
        <Surface variant="transparent" className="mt-4 flex justify-end">
          <Button
            type="button"
            variant="outline"
            onPress={onClear}
            className="min-h-9 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
          >
            <X className="size-4" aria-hidden />
            Clear filters
          </Button>
        </Surface>
      ) : null}
    </Surface>
  );
}

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <Typography.Paragraph className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
        {label}
      </Typography.Paragraph>
      {children}
    </label>
  );
}
