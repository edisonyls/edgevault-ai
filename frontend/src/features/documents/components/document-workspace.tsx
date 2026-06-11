"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useMemo, useState } from "react";
import { Link, Surface } from "@heroui/react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { WorkspaceHeader } from "@/components/layout/workspace-header";
import { DocumentChat } from "@/features/chat/components/document-chat";
import { initialMessages } from "@/features/chat/data/mock-messages";
import { uploadDocumentFile } from "../api/uploads";
import { initialDocuments } from "../data/mock-documents";
import { mapUploadToDocument, sumDetectedAmounts } from "../lib/document-utils";
import { DocumentList } from "./document-list";
import type { DocumentType, VaultDocument } from "../types/document";

export function DocumentWorkspace() {
  const [documents, setDocuments] = useState(initialDocuments);
  const [query, setQuery] = useState("");
  const [selectedType, setSelectedType] = useState<"All" | DocumentType>("All");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftName, setDraftName] = useState("");
  const [messages, setMessages] = useState(initialMessages);
  const [chatInput, setChatInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const filteredDocuments = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return documents.filter((document) => {
      const matchesType =
        selectedType === "All" || document.type === selectedType;
      const matchesQuery =
        normalizedQuery.length === 0 ||
        [document.name, document.vendor, document.type, document.status]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      return matchesType && matchesQuery;
    });
  }, [documents, query, selectedType]);

  const readyCount = documents.filter(
    (document) => document.status === "Ready",
  ).length;
  const reviewCount = documents.filter(
    (document) => document.status === "Review",
  ).length;

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";

    if (files.length === 0) {
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    const results = await Promise.allSettled(files.map(uploadDocumentFile));
    const uploadedDocuments: VaultDocument[] = [];
    const failedFileNames: string[] = [];

    results.forEach((result, index) => {
      if (result.status === "fulfilled") {
        uploadedDocuments.push(mapUploadToDocument(result.value));
        return;
      }

      failedFileNames.push(files[index].name);
    });

    if (uploadedDocuments.length > 0) {
      setDocuments((current) => [...uploadedDocuments, ...current]);
    }

    if (failedFileNames.length > 0) {
      setUploadError(
        `Could not upload ${failedFileNames.join(", ")}. Check the backend and try again.`,
      );
    }

    setIsUploading(false);
  }

  function startRename(document: VaultDocument) {
    setEditingId(document.id);
    setDraftName(document.name);
  }

  function saveRename(id: string) {
    const nextName = draftName.trim();

    if (!nextName) {
      return;
    }

    setDocuments((current) =>
      current.map((document) =>
        document.id === id ? { ...document, name: nextName } : document,
      ),
    );
    setEditingId(null);
    setDraftName("");
  }

  function deleteDocument(id: string) {
    setDocuments((current) => current.filter((document) => document.id !== id));
  }

  function handleChatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const question = chatInput.trim();

    if (!question) {
      return;
    }

    const totalAmount = sumDetectedAmounts(documents);

    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", text: question },
      {
        id: Date.now() + 1,
        role: "assistant",
        text: `Preview answer: I found ${documents.length} uploaded documents, ${reviewCount} marked for review, and about $${totalAmount.toFixed(
          2,
        )} across documents with detected totals.`,
      },
    ]);
    setChatInput("");
  }

  return (
    <Surface
      render={(props) => <main {...props} />}
      id="main-content"
      className="min-h-screen bg-[#f7f8fb] text-slate-950"
    >
      <Link
        href="#documents"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-3 focus:text-sm focus:font-semibold focus:text-slate-950 focus:ring-2 focus:ring-indigo-600"
      >
        Skip to document list
      </Link>

      <Surface
        variant="transparent"
        className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col lg:flex-row"
      >
        <AppSidebar
          documentCount={documents.length}
          readyCount={readyCount}
          reviewCount={reviewCount}
          onUpload={handleUpload}
          isUploading={isUploading}
          uploadError={uploadError}
        />

        <Surface
          render={(props) => <section {...props} />}
          variant="transparent"
          className="flex min-w-0 flex-1 flex-col"
        >
          <WorkspaceHeader
            documentCount={documents.length}
            readyCount={readyCount}
            reviewCount={reviewCount}
          />

          <Surface
            variant="transparent"
            className="grid min-h-0 flex-1 gap-0 xl:grid-cols-[minmax(0,1fr)_420px]"
          >
            <DocumentList
              documents={filteredDocuments}
              totalDocuments={documents.length}
              query={query}
              selectedType={selectedType}
              editingId={editingId}
              draftName={draftName}
              onQueryChange={setQuery}
              onSelectedTypeChange={setSelectedType}
              onDraftNameChange={setDraftName}
              onStartRename={startRename}
              onSaveRename={saveRename}
              onCancelRename={() => setEditingId(null)}
              onDelete={deleteDocument}
            />

            <DocumentChat
              messages={messages}
              input={chatInput}
              onInputChange={setChatInput}
              onSubmit={handleChatSubmit}
            />
          </Surface>
        </Surface>
      </Surface>
    </Surface>
  );
}
