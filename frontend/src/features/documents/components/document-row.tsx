import { Button, Chip, Input, Surface, Table, Typography } from "@heroui/react";
import { statusColor, typeColor } from "../lib/document-display";
import type { VaultDocument } from "../types/document";
import { DocumentActions } from "./document-actions";

type DocumentRowProps = {
  document: VaultDocument;
  isEditing: boolean;
  draftName: string;
  isPending: boolean;
  onDraftNameChange: (value: string) => void;
  onStartRename: (document: VaultDocument) => void;
  onSaveRename: (id: string) => void | Promise<void>;
  onCancelRename: () => void;
  onDelete: (id: string) => void | Promise<void>;
};

export function DocumentRow({
  document,
  isEditing,
  draftName,
  isPending,
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
                      void onSaveRename(document.id);
                    }
                    if (event.key === "Escape") {
                      onCancelRename();
                    }
                  }}
                  className="min-h-10 min-w-0 flex-1 rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600"
                  disabled={isPending}
                  autoFocus
                />
                <Button
                  type="button"
                  variant="primary"
                  onPress={() => void onSaveRename(document.id)}
                  isDisabled={isPending}
                  className="min-h-10 rounded-md bg-slate-950 px-3 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600"
                >
                  {isPending ? "Saving" : "Save"}
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
        <Surface variant="transparent" className="flex justify-end">
          <DocumentActions
            document={document}
            isPending={isPending}
            onStartRename={onStartRename}
            onDelete={onDelete}
          />
        </Surface>
      </Table.Cell>
    </Table.Row>
  );
}
