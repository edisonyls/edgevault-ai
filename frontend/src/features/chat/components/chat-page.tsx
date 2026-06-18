"use client";

import type { ChangeEvent } from "react";
import { useRef } from "react";
import { Link, Surface, Typography } from "@heroui/react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { SummaryTile } from "@/components/ui/summary-tile";
import { useDocuments } from "@/features/documents/hooks/use-documents";
import { useDocumentChat } from "../hooks/use-document-chat";
import { DocumentChat } from "./document-chat";

export function ChatPage() {
  const { documents, isUploading, uploadError, uploadFiles } = useDocuments();
  const chat = useDocumentChat();
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
      className="min-h-screen bg-[#f7f8fb] pb-20 text-slate-950 lg:pb-0"
    >
      <Link
        href="#chat"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-3 focus:text-sm focus:font-semibold focus:text-slate-950 focus:ring-2 focus:ring-indigo-600"
      >
        Skip to chat
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
          id="chat"
          variant="transparent"
          className="flex min-w-0 flex-1 flex-col"
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
                  Grounded in your records
                </Typography.Paragraph>
                <Typography.Heading
                  level={1}
                  className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl"
                >
                  AI chat
                </Typography.Heading>
                <Typography.Paragraph className="mt-2 text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
                  Ask about your spending — totals, unpaid bills, subscriptions,
                  and summaries, each backed by your uploaded documents.
                </Typography.Paragraph>
              </Surface>

              <Surface
                variant="transparent"
                className="grid grid-cols-2 gap-3 sm:min-w-[280px]"
              >
                <SummaryTile label="Files" value={documents.length} />
                <SummaryTile label="Ready" value={readyCount} />
              </Surface>
            </Surface>
          </Surface>

          <Surface
            variant="transparent"
            className="flex min-h-0 flex-1 px-5 py-6 sm:px-6 lg:px-8"
          >
            <Surface
              variant="transparent"
              className="mx-auto flex min-h-0 w-full max-w-4xl flex-1 overflow-hidden rounded-lg border border-slate-200"
            >
              <DocumentChat
                messages={chat.messages}
                input={chat.input}
                isSending={chat.isSending}
                onInputChange={chat.setInput}
                onSubmit={chat.submit}
              />
            </Surface>
          </Surface>
        </Surface>
      </Surface>
    </Surface>
  );
}
