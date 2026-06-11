import { Button, Surface } from "@heroui/react";
import { IconEdit, IconTrash } from "@/components/icons";
import type { VaultDocument } from "../types/document";

type DocumentActionsProps = {
  document: VaultDocument;
  isPending: boolean;
  onStartRename: (document: VaultDocument) => void;
  onDelete: (id: string) => void | Promise<void>;
};

export function DocumentActions({
  document,
  isPending,
  onStartRename,
  onDelete,
}: DocumentActionsProps) {
  return (
    <Surface variant="transparent" className="flex gap-2">
      <Button
        type="button"
        variant="outline"
        isIconOnly
        onPress={() => onStartRename(document)}
        isDisabled={isPending}
        aria-label={`Rename ${document.name}`}
        className="grid min-h-11 min-w-11 place-items-center rounded-md border border-slate-200 text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
      >
        <IconEdit className="size-4" />
      </Button>
      <Button
        type="button"
        variant="outline"
        isIconOnly
        onPress={() => void onDelete(document.id)}
        isDisabled={isPending}
        aria-label={`Delete ${document.name}`}
        className="grid min-h-11 min-w-11 place-items-center rounded-md border border-slate-200 text-slate-600 transition hover:border-rose-300 hover:text-rose-700 focus:ring-2 focus:ring-rose-500"
      >
        <IconTrash className="size-4" />
      </Button>
    </Surface>
  );
}
