"use client";

import type { ChangeEvent } from "react";
import { useRef } from "react";
import { Link, Surface, Typography } from "@heroui/react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { SummaryTile } from "@/components/ui/summary-tile";
import { useDocuments } from "../hooks/use-documents";
import { VendorRulesPanel } from "./vendor-rules-dialog";

export function VendorRulesPage() {
  const { documents, isUploading, uploadError, uploadFiles } = useDocuments();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const readyCount = documents.filter(
    (document) => document.status === "Ready",
  ).length;
  const failedCount = documents.filter(
    (document) => document.status === "Failed",
  ).length;

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
      className="min-h-screen bg-[#f7f8fb] text-slate-950"
    >
      <Link
        href="#vendors"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-3 focus:text-sm focus:font-semibold focus:text-slate-950 focus:ring-2 focus:ring-indigo-600"
      >
        Skip to vendor list
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
          id="vendors"
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
                  Matching rules
                </Typography.Paragraph>
                <Typography.Heading
                  level={1}
                  className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl"
                >
                  Vendors
                </Typography.Heading>
                <Typography.Paragraph className="mt-2 text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
                  Maintain the vendor names, keywords, and categories used
                  across financial documents.
                </Typography.Paragraph>
              </Surface>

              <Surface
                variant="transparent"
                className="grid grid-cols-3 gap-3 sm:min-w-[420px]"
              >
                <SummaryTile label="Files" value={documents.length} />
                <SummaryTile label="Ready" value={readyCount} />
                <SummaryTile label="Failed" value={failedCount} tone="amber" />
              </Surface>
            </Surface>
          </Surface>

          <Surface variant="transparent" className="px-5 py-6 sm:px-6 lg:px-8">
            <VendorRulesPanel className="max-w-6xl" />
          </Surface>
        </Surface>
      </Surface>
    </Surface>
  );
}
