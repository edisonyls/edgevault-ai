"use client";

import type { ChangeEvent } from "react";
import { useRef } from "react";
import { Button, Link, Separator, Surface, Typography } from "@heroui/react";
import { workspaceNavigation } from "@/config/navigation";
import { IconSpark, IconUpload } from "@/components/icons";
import { Metric } from "@/components/ui/summary-tile";

type AppSidebarProps = {
  documentCount: number;
  readyCount: number;
  reviewCount: number;
  onUpload: (event: ChangeEvent<HTMLInputElement>) => void;
  isUploading: boolean;
  uploadError: string | null;
};

export function AppSidebar({
  documentCount,
  readyCount,
  reviewCount,
  onUpload,
  isUploading,
  uploadError,
}: AppSidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <Surface
      render={(props) => <aside {...props} />}
      className="border-b border-slate-200 bg-white px-5 py-4 lg:w-64 lg:border-b-0 lg:border-r lg:px-6 lg:py-6"
    >
      <Surface
        variant="transparent"
        className="flex items-center justify-between gap-4 lg:block"
      >
        <Surface variant="transparent" className="flex items-center gap-3">
          <Surface
            variant="transparent"
            className="grid size-10 place-items-center rounded-md bg-slate-950 text-white"
          >
            <IconSpark className="size-5" />
          </Surface>
          <Surface variant="transparent">
            <Typography.Paragraph className="text-base font-semibold">
              EdgeVault AI
            </Typography.Paragraph>
            <Typography.Paragraph className="text-sm text-slate-500">
              Document workspace
            </Typography.Paragraph>
          </Surface>
        </Surface>

        <Button
          type="button"
          variant="primary"
          className="min-h-11 gap-2 rounded-md bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 lg:mt-8 lg:w-full"
          onPress={() => fileInputRef.current?.click()}
          isDisabled={isUploading}
        >
          <IconUpload className="size-4" />
          {isUploading ? "Uploading" : "Upload"}
        </Button>
        <input
          ref={fileInputRef}
          className="sr-only"
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.csv,.doc,.docx"
          onChange={onUpload}
          disabled={isUploading}
        />
        {uploadError && (
          <Typography.Paragraph
            role="alert"
            className="mt-3 max-w-full text-sm text-rose-700 lg:text-xs"
          >
            {uploadError}
          </Typography.Paragraph>
        )}
      </Surface>

      <nav className="mt-5 hidden space-y-1 lg:block" aria-label="Workspace">
        {workspaceNavigation.map((item) => (
          <Link
            key={item.label}
            href={item.href}
            className={`flex min-h-11 items-center rounded-md px-3 text-sm font-medium transition focus:ring-2 focus:ring-indigo-600 ${
              item.isActive
                ? "bg-slate-950 text-white"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      <Surface variant="transparent" className="mt-6 hidden lg:block">
        <Separator className="mb-6 bg-slate-200" />
        <Typography.Paragraph className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
          This month
        </Typography.Paragraph>
        <Surface variant="transparent" className="mt-4 space-y-4">
          <Metric label="Uploaded" value={String(documentCount)} />
          <Metric label="Ready to query" value={String(readyCount)} />
          <Metric label="Needs review" value={String(reviewCount)} />
        </Surface>
      </Surface>
    </Surface>
  );
}
