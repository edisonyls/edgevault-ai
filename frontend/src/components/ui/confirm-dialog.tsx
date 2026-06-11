"use client";

import { useEffect, useId, useRef } from "react";
import { Button, Surface, Typography } from "@heroui/react";

type ConfirmDialogProps = {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isConfirming?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  isConfirming = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const headingId = useId();
  const descriptionId = useId();
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    confirmRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isConfirming) {
        onCancel();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isConfirming, onCancel]);

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
        onClick={() => {
          if (!isConfirming) {
            onCancel();
          }
        }}
      />

      <Surface
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={headingId}
        aria-describedby={descriptionId}
        className="relative w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-xl"
      >
        <Typography.Heading
          level={2}
          id={headingId}
          className="text-lg font-semibold text-slate-950"
        >
          {title}
        </Typography.Heading>
        <Typography.Paragraph
          id={descriptionId}
          className="mt-2 text-sm leading-6 text-slate-600"
        >
          {description}
        </Typography.Paragraph>

        <Surface
          variant="transparent"
          className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"
        >
          <Button
            type="button"
            variant="outline"
            onPress={onCancel}
            isDisabled={isConfirming}
            className="min-h-11 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
          >
            {cancelLabel}
          </Button>
          <Button
            ref={confirmRef}
            type="button"
            variant="primary"
            onPress={onConfirm}
            isDisabled={isConfirming}
            className="min-h-11 rounded-md bg-rose-600 px-4 text-sm font-semibold text-white transition hover:bg-rose-700 focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 disabled:opacity-70"
          >
            {isConfirming ? "Deleting…" : confirmLabel}
          </Button>
        </Surface>
      </Surface>
    </Surface>
  );
}
