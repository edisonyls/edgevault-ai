"use client";

import { useEffect, useId, useRef } from "react";
import { Button, Chip, Surface, Typography } from "@heroui/react";
import { statusColor } from "../lib/document-display";
import type { VaultDocument } from "../types/document";
import { FinancialRecordPanel } from "./financial-record-panel";

type DocumentTextDialogProps = {
  document: VaultDocument | null;
  onClose: () => void;
  onRecordSaved: () => void;
};

export function DocumentTextDialog({
  document: doc,
  onClose,
  onRecordSaved,
}: DocumentTextDialogProps) {
  const headingId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!doc) {
      return;
    }

    closeRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [doc, onClose]);

  if (!doc) {
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
        className="relative flex max-h-[80vh] w-full max-w-2xl flex-col rounded-lg border border-slate-200 bg-white p-6 shadow-xl"
      >
        <Surface
          variant="transparent"
          className="flex items-start justify-between gap-4"
        >
          <Surface variant="transparent" className="min-w-0">
            <Typography.Heading
              level={2}
              id={headingId}
              className="truncate text-lg font-semibold text-slate-950"
            >
              {doc.name}
            </Typography.Heading>
            <Surface
              variant="transparent"
              className="mt-2 flex items-center gap-2"
            >
              <Chip
                color={statusColor(doc.status)}
                size="sm"
                variant="soft"
                className="rounded-md border text-xs font-semibold"
              >
                {doc.status}
              </Chip>
              <Typography.Paragraph size="xs" className="text-slate-500">
                Document detail
              </Typography.Paragraph>
            </Surface>
          </Surface>

          <Button
            ref={closeRef}
            type="button"
            variant="outline"
            onPress={onClose}
            className="min-h-10 shrink-0 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
          >
            Close
          </Button>
        </Surface>

        <Surface
          variant="transparent"
          className="mt-4 min-h-0 flex-1 space-y-5 overflow-auto pr-1"
        >
          <FinancialRecordPanel
            uploadId={doc.id}
            isProcessing={
              doc.status === "Processing" || doc.status === "Indexing"
            }
            onSaved={onRecordSaved}
          />

          <Surface variant="transparent">
            <Typography.Heading
              level={3}
              className="text-sm font-semibold uppercase tracking-[0.08em] text-slate-500"
            >
              Extracted text
            </Typography.Heading>
            <Surface
              variant="transparent"
              className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-4"
            >
              <DocumentTextBody document={doc} />
            </Surface>
          </Surface>
        </Surface>
      </Surface>
    </Surface>
  );
}

function DocumentTextBody({ document: doc }: { document: VaultDocument }) {
  if (doc.status === "Processing") {
    return (
      <Typography.Paragraph className="text-sm text-slate-500">
        Text extraction is still in progress. This view will update once it
        finishes.
      </Typography.Paragraph>
    );
  }

  if (doc.status === "Failed") {
    return (
      <Typography.Paragraph className="text-sm text-rose-700">
        Text extraction failed for this document. Try uploading it again.
      </Typography.Paragraph>
    );
  }

  const text = doc.text?.trim();

  if (!text) {
    return (
      <Typography.Paragraph className="text-sm text-slate-500">
        No text was extracted from this document.
      </Typography.Paragraph>
    );
  }

  return (
    <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-6 text-slate-800">
      {text}
    </pre>
  );
}
