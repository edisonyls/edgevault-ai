import { IconFile, IconSearch } from "@/components/icons";
import { DocumentRow } from "./document-row";
import { MobileDocumentCard } from "./mobile-document-card";
import type { DocumentType, VaultDocument } from "../types/document";

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
    <section
      id="documents"
      className="min-w-0 border-b border-slate-200 bg-[#f7f8fb] px-5 py-5 sm:px-6 lg:px-8 xl:border-b-0 xl:border-r"
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-950">
            Uploaded files
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {documents.length} of {totalDocuments} documents shown
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="relative block">
            <span className="sr-only">Search files</span>
            <IconSearch className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <input
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
              placeholder="Search files or vendors"
              className="min-h-11 w-full rounded-md border border-slate-300 bg-white py-2 pl-10 pr-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600 sm:w-72"
            />
          </label>

          <label className="sr-only" htmlFor="type-filter">
            Filter by document type
          </label>
          <select
            id="type-filter"
            value={selectedType}
            onChange={(event) =>
              onSelectedTypeChange(event.target.value as "All" | DocumentType)
            }
            className="min-h-11 rounded-md border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 outline-none transition focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
          >
            <option>All</option>
            <option>Bill</option>
            <option>Receipt</option>
            <option>Invoice</option>
            <option>Statement</option>
          </select>
        </div>
      </div>

      <div className="mt-5 overflow-hidden rounded-lg border border-slate-200 bg-white">
        <div className="hidden overflow-x-auto md:block">
          <table className="w-full min-w-[760px] border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3">
                  File
                </th>
                <th scope="col" className="px-4 py-3">
                  Vendor
                </th>
                <th scope="col" className="px-4 py-3">
                  Amount
                </th>
                <th scope="col" className="px-4 py-3">
                  Status
                </th>
                <th scope="col" className="px-4 py-3 text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
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
            </tbody>
          </table>
        </div>

        <div className="divide-y divide-slate-200 md:hidden">
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
        </div>

        {documents.length === 0 && <EmptyDocumentState />}
      </div>
    </section>
  );
}

function EmptyDocumentState() {
  return (
    <div className="px-6 py-12 text-center">
      <IconFile className="mx-auto size-10 text-slate-400" />
      <p className="mt-3 text-sm font-semibold text-slate-950">
        No documents match this view
      </p>
      <p className="mt-1 text-sm text-slate-500">
        Clear the search or choose a different file type.
      </p>
    </div>
  );
}
