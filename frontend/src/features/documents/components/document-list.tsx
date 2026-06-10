import {
  ListBox,
  SearchField,
  Select,
  Surface,
  Table,
  Typography,
} from "@heroui/react";
import { IconFile, IconSearch } from "@/components/icons";
import { DocumentRow } from "./document-row";
import { MobileDocumentCard } from "./mobile-document-card";
import type { DocumentType, VaultDocument } from "../types/document";

const documentTypes = [
  "All",
  "Bill",
  "Receipt",
  "Invoice",
  "Statement",
] as const;

type DocumentListProps = {
  documents: VaultDocument[];
  totalDocuments: number;
  query: string;
  selectedType: "All" | DocumentType;
  editingId: number | null;
  draftName: string;
  onQueryChange: (value: string) => void;
  onSelectedTypeChange: (value: "All" | DocumentType) => void;
  onDraftNameChange: (value: string) => void;
  onStartRename: (document: VaultDocument) => void;
  onSaveRename: (id: number) => void;
  onCancelRename: () => void;
  onDelete: (id: number) => void;
};

export function DocumentList({
  documents,
  totalDocuments,
  query,
  selectedType,
  editingId,
  draftName,
  onQueryChange,
  onSelectedTypeChange,
  onDraftNameChange,
  onStartRename,
  onSaveRename,
  onCancelRename,
  onDelete,
}: DocumentListProps) {
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
            {documents.length} of {totalDocuments} documents shown
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
              <SearchField.SearchIcon>
                <IconSearch className="size-4 text-slate-400" />
              </SearchField.SearchIcon>
              <SearchField.Input
                placeholder="Search files or vendors"
                className="min-w-0 flex-1 bg-transparent px-2 py-2 text-sm outline-none placeholder:text-slate-400"
              />
              <SearchField.ClearButton className="text-slate-400 hover:text-slate-700" />
            </SearchField.Group>
          </SearchField>

          <Select
            aria-label="Filter by document type"
            selectedKey={selectedType}
            onSelectionChange={(key) =>
              onSelectedTypeChange(String(key) as "All" | DocumentType)
            }
            className="w-full sm:w-44"
          >
            <Select.Trigger className="flex min-h-11 items-center justify-between rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:ring-2 focus:ring-indigo-600">
              <Select.Value />
              <Select.Indicator className="size-4 text-slate-500" />
            </Select.Trigger>
            <Select.Popover className="rounded-md border border-slate-200 bg-white p-1 shadow-lg">
              <ListBox className="outline-none">
                {documentTypes.map((type) => (
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

      <Surface className="mt-5 overflow-hidden rounded-lg border border-slate-200 bg-white">
        <Table className="hidden md:block">
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
              onDraftNameChange={onDraftNameChange}
              onStartRename={onStartRename}
              onSaveRename={onSaveRename}
              onCancelRename={onCancelRename}
              onDelete={onDelete}
            />
          ))}
        </Surface>

        {documents.length === 0 && <EmptyDocumentState />}
      </Surface>
    </Surface>
  );
}

function EmptyDocumentState() {
  return (
    <Surface variant="transparent" className="px-6 py-12 text-center">
      <IconFile className="mx-auto size-10 text-slate-400" />
      <Typography.Paragraph className="mt-3 text-sm font-semibold text-slate-950">
        No documents match this view
      </Typography.Paragraph>
      <Typography.Paragraph className="mt-1 text-sm text-slate-500">
        Clear the search or choose a different file type.
      </Typography.Paragraph>
    </Surface>
  );
}
