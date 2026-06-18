"use client";

import type { ChangeEvent } from "react";
import { useMemo, useRef, useState } from "react";
import { Link, Surface } from "@heroui/react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { WorkspaceHeader } from "@/components/layout/workspace-header";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useDocuments } from "../hooks/use-documents";
import type { DocumentTypeFilter, VaultDocument } from "../types/document";
import { DocumentList } from "./document-list";
import { DocumentTextDialog } from "./document-text-dialog";

export function DocumentWorkspace() {
  const {
    documents,
    isLoading,
    error,
    isUploading,
    uploadError,
    pendingId,
    clearError,
    reload,
    uploadFiles,
    renameDocument,
    deleteDocument,
  } = useDocuments();

  const [query, setQuery] = useState("");
  const [selectedType, setSelectedType] = useState<DocumentTypeFilter>("All");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftName, setDraftName] = useState("");
  const [viewingId, setViewingId] = useState<string | null>(null);
  const [deleteCandidate, setDeleteCandidate] = useState<VaultDocument | null>(
    null,
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  const failedCount = documents.filter(
    (document) => document.status === "Failed",
  ).length;

  const viewingDocument =
    documents.find((document) => document.id === viewingId) ?? null;

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function clearFilters() {
    setQuery("");
    setSelectedType("All");
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";

    await uploadFiles(files);
  }

  function viewDocument(document: VaultDocument) {
    setViewingId(document.id);
  }

  function startRename(document: VaultDocument) {
    clearError();
    setEditingId(document.id);
    setDraftName(document.name);
  }

  function cancelRename() {
    setEditingId(null);
    setDraftName("");
  }

  async function saveRename(id: string) {
    const nextName = draftName.trim();

    if (!nextName) {
      return;
    }

    const current = documents.find((document) => document.id === id);

    if (current?.name === nextName) {
      cancelRename();
      return;
    }

    if (await renameDocument(id, nextName)) {
      cancelRename();
    }
  }

  function requestDelete(id: string) {
    const candidate = documents.find((document) => document.id === id);

    if (candidate) {
      clearError();
      setDeleteCandidate(candidate);
    }
  }

  async function confirmDelete() {
    if (!deleteCandidate) {
      return;
    }

    const id = deleteCandidate.id;

    if (await deleteDocument(id)) {
      if (editingId === id) {
        cancelRename();
      }
    }

    setDeleteCandidate(null);
  }

  return (
    <Surface
      render={(props) => <main {...props} />}
      id="main-content"
      className="min-h-screen bg-[#f7f8fb] pb-20 text-slate-950 lg:pb-0"
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
          variant="transparent"
          className="flex min-w-0 flex-1 flex-col"
        >
          <WorkspaceHeader
            documentCount={documents.length}
            readyCount={readyCount}
            failedCount={failedCount}
          />

          <Surface variant="transparent" className="flex min-h-0 flex-1">
            <DocumentList
              documents={filteredDocuments}
              totalDocuments={documents.length}
              query={query}
              selectedType={selectedType}
              editingId={editingId}
              draftName={draftName}
              isLoading={isLoading}
              error={error}
              pendingDocumentId={pendingId}
              onQueryChange={setQuery}
              onSelectedTypeChange={setSelectedType}
              onDraftNameChange={setDraftName}
              onView={viewDocument}
              onStartRename={startRename}
              onSaveRename={saveRename}
              onCancelRename={cancelRename}
              onDelete={requestDelete}
              onClearFilters={clearFilters}
              onPickFiles={openFilePicker}
              isUploading={isUploading}
            />
          </Surface>
        </Surface>
      </Surface>

      <DocumentTextDialog
        document={viewingDocument}
        onClose={() => setViewingId(null)}
        onRecordSaved={() => void reload()}
      />

      <ConfirmDialog
        isOpen={deleteCandidate !== null}
        title="Delete this document?"
        description={
          deleteCandidate
            ? `“${deleteCandidate.name}” will be permanently removed. This can't be undone.`
            : ""
        }
        confirmLabel="Delete document"
        isConfirming={
          deleteCandidate !== null && pendingId === deleteCandidate.id
        }
        onConfirm={() => void confirmDelete()}
        onCancel={() => setDeleteCandidate(null)}
      />
    </Surface>
  );
}
