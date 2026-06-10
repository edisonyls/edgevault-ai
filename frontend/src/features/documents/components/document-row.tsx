import { Button, Chip, Input, Surface, Table, Typography } from "@heroui/react";
import { IconEdit, IconFile, IconTrash } from "@/components/icons";
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
    <Table.Row
      id={String(document.id)}
      className="align-middle transition hover:bg-slate-50"
    >
      <Table.Cell className="px-4 py-4">
        <Surface
          variant="transparent"
          className="flex min-w-0 items-start gap-3"
        >
          <Surface
            variant="transparent"
            className="grid size-10 shrink-0 place-items-center rounded-md bg-slate-100 text-slate-600"
          >
            <IconFile className="size-5" />
          </Surface>
          <Surface variant="transparent" className="min-w-0">
            {isEditing ? (
              <Surface
                variant="transparent"
                className="flex min-w-[280px] gap-2"
              >
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
                  className="min-h-10 min-w-0 flex-1 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
                  autoFocus
                />
                <Button
                  type="button"
                  variant="primary"
                  onPress={() => onSaveRename(document.id)}
                  className="min-h-10 rounded-md bg-slate-950 px-3 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600"
                >
                  Save
                </Button>
              </Surface>
            ) : (
              <Typography.Paragraph className="truncate font-semibold text-slate-950">
                {document.name}
              </Typography.Paragraph>
            )}
            <Surface
              variant="transparent"
              className="mt-2 flex flex-wrap items-center gap-2"
            >
              <Chip
                color={typeColor(document.type)}
                size="sm"
                variant="soft"
                className="rounded-md text-xs font-semibold"
              >
                {document.type}
              </Chip>
              <Typography.Paragraph size="xs" className="text-slate-500">
                {document.size}
              </Typography.Paragraph>
              <Typography.Paragraph size="xs" className="text-slate-500">
                {document.uploadedAt}
              </Typography.Paragraph>
            </Surface>
          </Surface>
        </Surface>
      </Table.Cell>
      <Table.Cell className="px-4 py-4 font-medium text-slate-700">
        {document.vendor}
      </Table.Cell>
      <Table.Cell className="px-4 py-4 font-semibold text-slate-950">
        {document.amount}
      </Table.Cell>
      <Table.Cell className="px-4 py-4">
        <Chip
          color={statusColor(document.status)}
          size="sm"
          variant="soft"
          className="rounded-md border text-xs font-semibold"
        >
          {document.status}
        </Chip>
      </Table.Cell>
      <Table.Cell className="px-4 py-4">
        <Surface variant="transparent" className="flex justify-end gap-2">
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
      </Table.Cell>
    </Table.Row>
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
