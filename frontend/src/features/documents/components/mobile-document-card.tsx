import { Button, Chip, Input, Surface, Typography } from "@heroui/react";
import { IconEdit, IconFile, IconTrash } from "@/components/icons";
import { Detail } from "@/components/ui/detail";
import type { VaultDocument } from "../types/document";

type MobileDocumentCardProps = {
  document: VaultDocument;
  isEditing: boolean;
  draftName: string;
  onDraftNameChange: (value: string) => void;
  onStartRename: (document: VaultDocument) => void;
  onSaveRename: (id: string) => void;
  onCancelRename: () => void;
  onDelete: (id: string) => void;
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
    <Surface
      render={(props) => <article {...props} />}
      variant="transparent"
      className="p-4"
    >
      <Surface variant="transparent" className="flex gap-3">
        <Surface
          variant="transparent"
          className="grid size-10 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600"
        >
          <IconFile className="size-5" />
        </Surface>
        <Surface variant="transparent" className="min-w-0 flex-1">
          {isEditing ? (
            <Surface variant="transparent" className="space-y-2">
              <Input
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
              <Button
                type="button"
                variant="primary"
                onPress={() => onSaveRename(document.id)}
                className="min-h-11 w-full rounded-md bg-slate-950 px-3 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600"
              >
                Save name
              </Button>
            </Surface>
          ) : (
            <Typography.Heading
              level={3}
              className="break-words text-sm font-semibold leading-6 text-slate-950"
            >
              {document.name}
            </Typography.Heading>
          )}
          <Typography.Paragraph className="mt-1 text-sm text-slate-500">
            {document.vendor}
          </Typography.Paragraph>
        </Surface>
      </Surface>

      <Surface
        variant="transparent"
        className="mt-4 grid grid-cols-2 gap-2 text-sm"
      >
        <Detail label="Amount" value={document.amount} />
        <Detail label="Uploaded" value={document.uploadedAt} />
      </Surface>

      <Surface
        variant="transparent"
        className="mt-4 flex flex-wrap items-center justify-between gap-3"
      >
        <Surface variant="transparent" className="flex flex-wrap gap-2">
          <Chip
            color={typeColor(document.type)}
            size="sm"
            variant="soft"
            className="rounded-md text-xs font-semibold"
          >
            {document.type}
          </Chip>
          <Chip
            color={statusColor(document.status)}
            size="sm"
            variant="soft"
            className="rounded-md border text-xs font-semibold"
          >
            {document.status}
          </Chip>
        </Surface>
        <Surface variant="transparent" className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            isIconOnly
            onPress={() => onStartRename(document)}
            aria-label={`Rename ${document.name}`}
            className="grid min-h-11 min-w-11 place-items-center rounded-md border border-slate-200 text-slate-600 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
          >
            <IconEdit className="size-4" />
          </Button>
          <Button
            type="button"
            variant="outline"
            isIconOnly
            onPress={() => onDelete(document.id)}
            aria-label={`Delete ${document.name}`}
            className="grid min-h-11 min-w-11 place-items-center rounded-md border border-slate-200 text-slate-600 transition hover:border-rose-300 hover:text-rose-700 focus:ring-2 focus:ring-rose-500"
          >
            <IconTrash className="size-4" />
          </Button>
        </Surface>
      </Surface>
    </Surface>
  );
}

function typeColor(type: VaultDocument["type"]) {
  switch (type) {
    case "Bill":
      return "accent";
    case "Invoice":
      return "success";
    case "Receipt":
      return "default";
    case "Statement":
      return "warning";
  }
}

function statusColor(status: VaultDocument["status"]) {
  switch (status) {
    case "Ready":
      return "success";
    case "Review":
      return "warning";
    case "Processing":
      return "accent";
  }
}
