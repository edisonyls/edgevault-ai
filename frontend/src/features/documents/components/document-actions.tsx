import { Button, Surface } from "@heroui/react";
import type { VaultDocument } from "../types/document";

type DocumentActionsProps = {
  document: VaultDocument;
  isPending: boolean;
  onView: (document: VaultDocument) => void;
  onStartRename: (document: VaultDocument) => void;
  onDelete: (id: string) => void | Promise<void>;
};

export function DocumentActions({
  document,
  isPending,
  onView,
  onStartRename,
  onDelete,
}: DocumentActionsProps) {
  return (
    <Surface variant="transparent" className="flex gap-2">
      <Button
        type="button"
        variant="outline"
        onPress={() => onView(document)}
        aria-label={`View extracted text for ${document.name}`}
        className="grid min-h-11 place-items-center rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
      >
        View
      </Button>
      <Button
        type="button"
        variant="outline"
        onPress={() => onStartRename(document)}
        isDisabled={isPending}
        aria-label={`Rename ${document.name}`}
        className="grid min-h-11 place-items-center rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
      >
        Rename
      </Button>
      <Button
        type="button"
        variant="outline"
        onPress={() => void onDelete(document.id)}
        isDisabled={isPending}
        aria-label={`Delete ${document.name}`}
        className="grid min-h-11 place-items-center rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:border-rose-300 hover:text-rose-700 focus:ring-2 focus:ring-rose-500"
      >
        Delete
      </Button>
    </Surface>
  );
}
