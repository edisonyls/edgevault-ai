import { IconEdit, IconFile, IconTrash } from "@/components/icons";
import { Detail } from "@/components/ui/detail";
import { statusStyles, typeStyles } from "../lib/document-styles";
import type { VaultDocument } from "../types/document";

type MobileDocumentCardProps = {
  document: VaultDocument;
  isEditing: boolean;
  draftName: string;
  onDraftNameChange: (value: string) => void;
  onStartRename: (document: VaultDocument) => void;
  onSaveRename: (id: number) => void;
  onCancelRename: () => void;
  onDelete: (id: number) => void;
};

export function MobileDocumentCard({
  document,
  isEditing,
  draftName,
  onDraftNameChange,
  onStartRename,
  onSaveRename,
  onCancelRename,
  onDelete,
}: MobileDocumentCardProps) {
  return (
    <article className="p-4">
      <div className="flex gap-3">
        <div className="grid size-10 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600">
          <IconFile className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          {isEditing ? (
            <div className="space-y-2">
              <input
                value={draftName}
                onChange={(event) => onDraftNameChange(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    onSaveRename(document.id);
                  }
                  if (event.key === "Escape") {
                    onCancelRename();
                  }
                }}
                className="min-h-11 w-full rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
                autoFocus
              />
              <button
                type="button"
                onClick={() => onSaveRename(document.id)}
                className="min-h-11 w-full rounded-md bg-slate-950 px-3 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600"
              >
                Save name
              </button>
            </div>
          ) : (
            <h3 className="break-words text-sm font-semibold leading-6 text-slate-950">
              {document.name}
            </h3>
          )}
          <p className="mt-1 text-sm text-slate-500">{document.vendor}</p>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <Detail label="Amount" value={document.amount} />
        <Detail label="Uploaded" value={document.uploadedAt} />
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          <span
            className={`rounded-md px-2 py-1 text-xs font-semibold ${typeStyles[document.type]}`}
          >
            {document.type}
          </span>
          <span
            className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${statusStyles[document.status]}`}
          >
            {document.status}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onStartRename(document)}
            aria-label={`Rename ${document.name}`}
            className="grid min-h-11 min-w-11 place-items-center rounded-md border border-slate-200 text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
          >
            <IconEdit className="size-4" />
          </button>
          <button
            type="button"
            onClick={() => onDelete(document.id)}
            aria-label={`Delete ${document.name}`}
            className="grid min-h-11 min-w-11 place-items-center rounded-md border border-slate-200 text-slate-600 transition hover:border-rose-300 hover:text-rose-700 focus:ring-2 focus:ring-rose-500"
          >
            <IconTrash className="size-4" />
          </button>
        </div>
      </div>
    </article>
  );
}
