import {
  Button,
  ListBox,
  SearchField,
  Select,
  Surface,
  Table,
  Typography,
} from "@heroui/react";
import { DocumentListSkeleton } from "./document-list-skeleton";
import { DocumentRow } from "./document-row";
import { MobileDocumentCard } from "./mobile-document-card";
import {
  DOCUMENT_TYPE_FILTERS,
  type DocumentTypeFilter,
  type VaultDocument,
} from "../types/document";

type DocumentListProps = {
  documents: VaultDocument[];
  totalDocuments: number;
  query: string;
  selectedType: DocumentTypeFilter;
  editingId: string | null;
  draftName: string;
  isLoading: boolean;
  error: string | null;
  pendingDocumentId: string | null;
  onQueryChange: (value: string) => void;
  onSelectedTypeChange: (value: DocumentTypeFilter) => void;
  onDraftNameChange: (value: string) => void;
  onStartRename: (document: VaultDocument) => void;
  onSaveRename: (id: string) => void | Promise<void>;
  onCancelRename: () => void;
  onDelete: (id: string) => void | Promise<void>;
  onClearFilters: () => void;
  onPickFiles: () => void;
  isUploading: boolean;
};

export function DocumentList({
  documents,
  totalDocuments,
  query,
  selectedType,
  editingId,
  draftName,
  isLoading,
  error,
  pendingDocumentId,
  onQueryChange,
  onSelectedTypeChange,
  onDraftNameChange,
  onStartRename,
  onSaveRename,
  onCancelRename,
  onDelete,
  onClearFilters,
  onPickFiles,
  isUploading,
}: DocumentListProps) {
  const hasActiveFilters = query.trim().length > 0 || selectedType !== "All";

  return (
    <Surface
      render={(props) => <section {...props} />}
      id="documents"
      className="min-w-0 border-b border-slate-200 bg-[#f7f8fb] px-5 py-5 sm:px-6 lg:px-8 xl:border-b-0 xl:border-r"
    >
      <Surface
        variant="transparent"
        className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
      >
        <Surface variant="transparent">
          <Typography.Heading
            level={2}
            className="text-xl font-semibold text-slate-950"
          >
            Uploaded files
          </Typography.Heading>
          <Typography.Paragraph className="mt-1 text-sm text-slate-500">
            {isLoading
              ? "Loading uploads"
              : `${documents.length} of ${totalDocuments} documents shown`}
          </Typography.Paragraph>
        </Surface>

        <Surface
          variant="transparent"
          className="flex flex-col gap-3 sm:flex-row sm:items-center"
        >
          <SearchField
            value={query}
            onChange={onQueryChange}
            aria-label="Search files"
            className="w-full sm:w-72"
          >
            <SearchField.Group className="flex min-h-11 items-center rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-950 transition focus-within:border-indigo-600 focus-within:ring-2 focus-within:ring-indigo-600">
              <SearchField.Input
                placeholder="Search files or vendors"
                className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm outline-none placeholder:text-slate-400"
              />
              <SearchField.ClearButton className="text-slate-400 hover:text-slate-700" />
            </SearchField.Group>
          </SearchField>

          <Select
            aria-label="Filter by document type"
            selectedKey={selectedType}
            onSelectionChange={(key) =>
              onSelectedTypeChange(String(key) as DocumentTypeFilter)
            }
            className="w-full sm:w-44"
          >
            <Select.Trigger className="flex min-h-11 items-center justify-between rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:ring-2 focus:ring-indigo-600">
              <Select.Value />
              <Select.Indicator className="size-4 text-slate-500" />
            </Select.Trigger>
            <Select.Popover className="rounded-md border border-slate-200 bg-white p-1 shadow-lg">
              <ListBox className="outline-none">
                {DOCUMENT_TYPE_FILTERS.map((type) => (
                  <ListBox.Item
                    key={type}
                    id={type}
                    className="rounded-md px-3 py-2 text-sm text-slate-700 outline-none hover:bg-slate-100 focus:bg-slate-100"
                  >
                    {type}
                  </ListBox.Item>
                ))}
              </ListBox>
            </Select.Popover>
          </Select>
        </Surface>
      </Surface>

      {error && (
        <Typography.Paragraph
          role="alert"
          className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
        >
          {error}
        </Typography.Paragraph>
      )}

      <Surface className="mt-5 overflow-hidden rounded-lg border border-slate-200 bg-white">
        {isLoading ? (
          <DocumentListSkeleton />
        ) : documents.length === 0 ? (
          <EmptyDocumentState
            hasActiveFilters={hasActiveFilters}
            isUploading={isUploading}
            onClearFilters={onClearFilters}
            onPickFiles={onPickFiles}
          />
        ) : (
          <>
            <Table variant="secondary" className="hidden md:block">
              <Table.ScrollContainer className="overflow-x-auto">
                <Table.Content
                  aria-label="Uploaded files"
                  className="w-full min-w-[760px] border-collapse text-left text-sm"
                >
                  <Table.Header className="bg-slate-50 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
                    <Table.Column isRowHeader className="px-4 py-3">
                      File
                    </Table.Column>
                    <Table.Column className="px-4 py-3">Vendor</Table.Column>
                    <Table.Column className="px-4 py-3">Amount</Table.Column>
                    <Table.Column className="px-4 py-3">Status</Table.Column>
                    <Table.Column className="px-4 py-3 text-right">
                      Actions
                    </Table.Column>
                  </Table.Header>
                  <Table.Body className="divide-y divide-slate-200">
                    {documents.map((document) => (
                      <DocumentRow
                        key={document.id}
                        document={document}
                        isEditing={editingId === document.id}
                        draftName={draftName}
                        isPending={pendingDocumentId === document.id}
                        onDraftNameChange={onDraftNameChange}
                        onStartRename={onStartRename}
                        onSaveRename={onSaveRename}
                        onCancelRename={onCancelRename}
                        onDelete={onDelete}
                      />
                    ))}
                  </Table.Body>
                </Table.Content>
              </Table.ScrollContainer>
            </Table>

            <Surface
              variant="transparent"
              className="divide-y divide-slate-200 md:hidden"
            >
              {documents.map((document) => (
                <MobileDocumentCard
                  key={document.id}
                  document={document}
                  isEditing={editingId === document.id}
                  draftName={draftName}
                  isPending={pendingDocumentId === document.id}
                  onDraftNameChange={onDraftNameChange}
                  onStartRename={onStartRename}
                  onSaveRename={onSaveRename}
                  onCancelRename={onCancelRename}
                  onDelete={onDelete}
                />
              ))}
            </Surface>
          </>
        )}
      </Surface>
    </Surface>
  );
}

type EmptyDocumentStateProps = {
  hasActiveFilters: boolean;
  isUploading: boolean;
  onClearFilters: () => void;
  onPickFiles: () => void;
};

function EmptyDocumentState({
  hasActiveFilters,
  isUploading,
  onClearFilters,
  onPickFiles,
}: EmptyDocumentStateProps) {
  return (
    <Surface
      variant="transparent"
      className="flex flex-col items-center px-6 py-16 text-center"
    >
      <Typography.Paragraph className="text-base font-semibold text-slate-950">
        {hasActiveFilters
          ? "No documents match your filters"
          : "No documents yet"}
      </Typography.Paragraph>
      <Typography.Paragraph className="mt-1 max-w-sm text-sm text-slate-500">
        {hasActiveFilters
          ? "Try a different search term or file type to see more results."
          : "Upload bills, receipts, invoices, or statements to start reviewing and querying them."}
      </Typography.Paragraph>

      {hasActiveFilters ? (
        <Button
          type="button"
          variant="outline"
          onPress={onClearFilters}
          className="mt-5 min-h-11 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
        >
          Clear filters
        </Button>
      ) : (
        <Button
          type="button"
          variant="primary"
          onPress={onPickFiles}
          isDisabled={isUploading}
          className="mt-5 min-h-11 rounded-md bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2"
        >
          {isUploading ? "Uploading…" : "Upload your first document"}
        </Button>
      )}
    </Surface>
  );
}
