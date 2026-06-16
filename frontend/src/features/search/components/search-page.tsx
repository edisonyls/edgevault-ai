"use client";

import type { ChangeEvent } from "react";
import { useMemo, useRef, useState } from "react";
import { Link, Surface, Typography } from "@heroui/react";
import { AlertCircle, SearchX } from "lucide-react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { SummaryTile } from "@/components/ui/summary-tile";
import { DocumentTextDialog } from "@/features/documents/components/document-text-dialog";
import { useDocuments } from "@/features/documents/hooks/use-documents";
import { mapUploadToDocument } from "@/features/documents/lib/document-utils";
import { EMPTY_SEARCH_FILTERS } from "../types/search";
import type { SearchResult } from "../types/search";
import { useSearch } from "../hooks/use-search";
import { SearchFiltersBar } from "./search-filters";
import { SearchResultCard } from "./search-result-card";

export function SearchPage() {
  const { documents, isUploading, uploadError, uploadFiles, reload } =
    useDocuments();
  const { filters, results, isLoading, error, setFilters, clearFilters } =
    useSearch();
  const [openResult, setOpenResult] = useState<SearchResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const readyCount = documents.filter(
    (document) => document.status === "Ready",
  ).length;
  const failedCount = documents.filter(
    (document) => document.status === "Failed",
  ).length;

  const hasActiveFilters = useMemo(
    () => JSON.stringify(filters) !== JSON.stringify(EMPTY_SEARCH_FILTERS),
    [filters],
  );

  const openDocument = useMemo(() => {
    if (!openResult) {
      return null;
    }

    return mapUploadToDocument(openResult.upload, openResult.financial_record);
  }, [openResult]);

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";

    await uploadFiles(files);
  }

  return (
    <Surface
      render={(props) => <main {...props} />}
      id="main-content"
      className="min-h-screen bg-[#f7f8fb] pb-20 text-slate-950 lg:pb-0"
    >
      <Link
        href="#search"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-3 focus:text-sm focus:font-semibold focus:text-slate-950 focus:ring-2 focus:ring-indigo-600"
      >
        Skip to search results
      </Link>

      <Surface
        variant="transparent"
        className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col lg:flex-row"
      >
        <AppSidebar
          documentCount={documents.length}
          readyCount={readyCount}
          failedCount={failedCount}
          onPickFiles={openFilePicker}
          isUploading={isUploading}
          uploadError={uploadError}
        />

        <input
          ref={fileInputRef}
          className="sr-only"
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.csv,.doc,.docx"
          onChange={handleUpload}
          disabled={isUploading}
        />

        <Surface
          render={(props) => <section {...props} />}
          id="search"
          variant="transparent"
          className="min-w-0 flex-1"
        >
          <Surface
            render={(props) => <header {...props} />}
            className="border-b border-slate-200 bg-white px-5 py-6 sm:px-6 lg:px-8"
          >
            <Surface
              variant="transparent"
              className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between"
            >
              <Surface variant="transparent" className="max-w-3xl">
                <Typography.Paragraph className="text-sm font-semibold text-indigo-700">
                  Find anything
                </Typography.Paragraph>
                <Typography.Heading
                  level={1}
                  className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl"
                >
                  Search
                </Typography.Heading>
                <Typography.Paragraph className="mt-2 text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
                  Search across the extracted text of every document, then
                  narrow by category, vendor, type, or date.
                </Typography.Paragraph>
              </Surface>

              <Surface
                variant="transparent"
                className="grid grid-cols-3 gap-3 sm:min-w-[420px]"
              >
                <SummaryTile label="Files" value={documents.length} />
                <SummaryTile label="Ready" value={readyCount} />
                <SummaryTile label="Matches" value={results.length} />
              </Surface>
            </Surface>
          </Surface>

          <Surface
            variant="transparent"
            className="space-y-6 px-5 py-6 sm:px-6 lg:px-8"
          >
            <SearchFiltersBar
              filters={filters}
              hasActiveFilters={hasActiveFilters}
              onChange={setFilters}
              onClear={clearFilters}
            />

            <SearchResults
              results={results}
              isLoading={isLoading}
              error={error}
              onOpen={setOpenResult}
            />
          </Surface>
        </Surface>
      </Surface>

      <DocumentTextDialog
        document={openDocument}
        onClose={() => setOpenResult(null)}
        onRecordSaved={() => void reload()}
      />
    </Surface>
  );
}

type SearchResultsProps = {
  results: SearchResult[];
  isLoading: boolean;
  error: string | null;
  onOpen: (result: SearchResult) => void;
};

function SearchResults({
  results,
  isLoading,
  error,
  onOpen,
}: SearchResultsProps) {
  if (error) {
    return (
      <Surface
        variant="transparent"
        role="alert"
        className="flex items-start gap-3 rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-700"
      >
        <AlertCircle className="mt-0.5 size-5 shrink-0" aria-hidden />
        <Typography.Paragraph className="text-sm">{error}</Typography.Paragraph>
      </Surface>
    );
  }

  if (isLoading) {
    return (
      <Surface variant="transparent" className="space-y-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="h-28 animate-pulse rounded-lg border border-slate-200 bg-white"
          />
        ))}
      </Surface>
    );
  }

  if (results.length === 0) {
    return (
      <Surface
        variant="transparent"
        className="grid min-h-72 place-items-center rounded-lg border border-dashed border-slate-300 bg-white px-4 py-10 text-center"
      >
        <Surface variant="transparent" className="max-w-sm">
          <Surface
            variant="transparent"
            className="mx-auto grid size-12 place-items-center rounded-lg bg-slate-100 text-slate-500"
          >
            <SearchX className="size-5" aria-hidden />
          </Surface>
          <Typography.Heading
            level={3}
            className="mt-4 text-base font-semibold text-slate-950"
          >
            No matching documents
          </Typography.Heading>
          <Typography.Paragraph className="mt-2 text-sm leading-6 text-slate-500">
            Try a different keyword or loosen the filters.
          </Typography.Paragraph>
        </Surface>
      </Surface>
    );
  }

  return (
    <Surface variant="transparent" className="space-y-3">
      {results.map((result) => (
        <SearchResultCard
          key={result.upload.id}
          result={result}
          onOpen={onOpen}
        />
      ))}
    </Surface>
  );
}
