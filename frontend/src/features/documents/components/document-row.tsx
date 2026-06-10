import { IconEdit, IconFile, IconTrash } from "@/components/icons";
import { statusStyles, typeStyles } from "../lib/document-styles";
import type { VaultDocument } from "../types/document";

type DocumentRowProps = {
  document: VaultDocument;
  isEditing: boolean;
  draftName: string;
  onDraftNameChange: (value: string) => void;
  onStartRename: (document: VaultDocument) => void;
  onSaveRename: (id: number) => void;
  onCancelRename: () => void;
  onDelete: (id: number) => void;
};

export function DocumentRow({
  document,
  isEditing,
  draftName,
  onDraftNameChange,
  onStartRename,
  onSaveRename,
  onCancelRename,
  onDelete,
}: DocumentRowProps) {
  return (
    <tr className="align-middle transition hover:bg-slate-50">
      <td className="px-4 py-4">
        <div className="flex min-w-0 items-start gap-3">
          <div className="grid size-10 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600">
            <IconFile className="size-5" />
          </div>
          <div className="min-w-0">
            {isEditing ? (
              <div className="flex min-w-[280px] gap-2">
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
                  className="min-h-10 min-w-0 flex-1 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => onSaveRename(document.id)}
                  className="min-h-10 rounded-md bg-slate-950 px-3 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600"
                >
                  Save
                </button>
              </div>
            ) : (
              <p className="truncate font-semibold text-slate-950">
                {document.name}
              </p>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span
                className={`rounded-md px-2 py-1 text-xs font-semibold ${typeStyles[document.type]}`}
              >
                {document.type}
              </span>
              <span className="text-xs text-slate-500">{document.size}</span>
              <span className="text-xs text-slate-500">
                {document.uploadedAt}
              </span>
            </div>
          </div>
        </div>
      </td>
      <td className="px-4 py-4 font-medium text-slate-700">
        {document.vendor}
      </td>
      <td className="px-4 py-4 font-semibold text-slate-950">
        {document.amount}
      </td>
      <td className="px-4 py-4">
        <span
          className={`inline-flex rounded-md border px-2.5 py-1 text-xs font-semibold ${statusStyles[document.status]}`}
        >
          {document.status}
        </span>
      </td>
      <td className="px-4 py-4">
        <div className="flex justify-end gap-2">
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
      </td>
    </tr>
  );
}
