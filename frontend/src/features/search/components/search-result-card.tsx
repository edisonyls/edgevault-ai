"use client";

import { Fragment } from "react";
import { Chip, Surface, Typography } from "@heroui/react";
import { FileText } from "lucide-react";
import {
  categoryLabel,
  documentTypeLabel,
  formatCurrencyAmount,
  formatRecordDate,
} from "@/features/documents/lib/financial-display";
import type { SearchResult } from "../types/search";

type SearchResultCardProps = {
  result: SearchResult;
  onOpen: (result: SearchResult) => void;
};

export function SearchResultCard({ result, onOpen }: SearchResultCardProps) {
  const { upload, financial_record: record, snippet } = result;
  const vendor = record?.vendor?.trim();
  const amount =
    record && record.total_amount !== null
      ? formatCurrencyAmount(record.total_amount, record.currency)
      : null;

  return (
    <button
      type="button"
      onClick={() => onOpen(result)}
      className="block w-full rounded-lg border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-indigo-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-600 sm:p-5"
    >
      <Surface variant="transparent" className="flex items-start gap-3">
        <Surface
          variant="transparent"
          className="grid size-10 shrink-0 place-items-center rounded-md bg-indigo-50 text-indigo-700"
        >
          <FileText className="size-5" aria-hidden />
        </Surface>

        <Surface variant="transparent" className="min-w-0 flex-1">
          <Surface
            variant="transparent"
            className="flex flex-wrap items-start justify-between gap-2"
          >
            <Typography.Heading
              level={3}
              className="min-w-0 truncate text-base font-semibold text-slate-950"
            >
              {upload.display_filename}
            </Typography.Heading>
            {amount ? (
              <Typography.Paragraph className="shrink-0 text-base font-semibold text-slate-950">
                {amount}
              </Typography.Paragraph>
            ) : null}
          </Surface>

          <Surface
            variant="transparent"
            className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500"
          >
            {vendor ? (
              <span className="font-medium text-slate-700">{vendor}</span>
            ) : null}
            {record?.document_type ? (
              <Chip
                size="sm"
                variant="soft"
                className="rounded-md bg-slate-100 text-xs font-semibold text-slate-700"
              >
                {documentTypeLabel(record.document_type)}
              </Chip>
            ) : null}
            {record?.category ? (
              <Chip
                size="sm"
                variant="soft"
                className="rounded-md bg-indigo-50 text-xs font-semibold text-indigo-700"
              >
                {categoryLabel(record.category)}
              </Chip>
            ) : null}
            {record?.transaction_date ? (
              <span>{formatRecordDate(record.transaction_date)}</span>
            ) : null}
          </Surface>

          {snippet ? (
            <Typography.Paragraph className="mt-3 line-clamp-2 text-sm leading-6 text-slate-600">
              <HighlightedSnippet snippet={snippet} />
            </Typography.Paragraph>
          ) : null}
        </Surface>
      </Surface>
    </button>
  );
}

function HighlightedSnippet({ snippet }: { snippet: string }) {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let key = 0;

  for (const match of snippet.matchAll(/<mark>(.*?)<\/mark>/g)) {
    const index = match.index ?? 0;
    if (index > lastIndex) {
      parts.push(
        <Fragment key={key++}>{snippet.slice(lastIndex, index)}</Fragment>,
      );
    }
    parts.push(
      <mark
        key={key++}
        className="rounded bg-amber-100 px-0.5 font-semibold text-slate-900"
      >
        {match[1]}
      </mark>,
    );
    lastIndex = index + match[0].length;
  }

  if (lastIndex < snippet.length) {
    parts.push(<Fragment key={key++}>{snippet.slice(lastIndex)}</Fragment>);
  }

  return <>{parts}</>;
}
