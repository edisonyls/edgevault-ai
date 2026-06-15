"use client";

import type { ReactNode } from "react";
import { Button, Chip, Input, Surface, Typography } from "@heroui/react";
import { Detail } from "@/components/ui/detail";
import type { FinancialRecord } from "../types/financial-record";
import {
  CATEGORY_OPTIONS,
  DOCUMENT_TYPE_OPTIONS,
  PAYMENT_STATUS_OPTIONS,
  categoryLabel,
  documentTypeLabel,
  formatConfidence,
  formatCurrencyAmount,
  formatRecordDate,
  paymentStatusLabel,
} from "../lib/financial-display";
import {
  type FinancialRecordDraft,
  useFinancialRecord,
} from "../hooks/use-financial-record";

type FinancialRecordPanelProps = {
  uploadId: string;
  isProcessing: boolean;
  onSaved: () => void;
};

const FIELD_CLASS =
  "min-h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600";

export function FinancialRecordPanel({
  uploadId,
  isProcessing,
  onSaved,
}: FinancialRecordPanelProps) {
  const {
    record,
    isLoading,
    loadError,
    isEditing,
    isSaving,
    saveError,
    draft,
    startEdit,
    cancelEdit,
    updateDraft,
    save,
  } = useFinancialRecord(uploadId, onSaved);

  return (
    <Surface variant="transparent">
      <Surface
        variant="transparent"
        className="flex items-center justify-between gap-3"
      >
        <Typography.Heading
          level={3}
          className="text-sm font-semibold uppercase tracking-[0.08em] text-slate-500"
        >
          Structured data
        </Typography.Heading>

        {record && !isEditing ? (
          <Button
            type="button"
            variant="outline"
            onPress={startEdit}
            className="min-h-9 shrink-0 rounded-md border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 focus:ring-2 focus:ring-indigo-600"
          >
            Edit
          </Button>
        ) : null}
      </Surface>

      <Surface variant="transparent" className="mt-3">
        <PanelBody
          record={record}
          isLoading={isLoading}
          loadError={loadError}
          isProcessing={isProcessing}
          isEditing={isEditing}
          isSaving={isSaving}
          saveError={saveError}
          draft={draft}
          onCancel={cancelEdit}
          onChange={updateDraft}
          onSave={() => void save()}
        />
      </Surface>
    </Surface>
  );
}

type PanelBodyProps = {
  record: FinancialRecord | null;
  isLoading: boolean;
  loadError: string | null;
  isProcessing: boolean;
  isEditing: boolean;
  isSaving: boolean;
  saveError: string | null;
  draft: FinancialRecordDraft | null;
  onCancel: () => void;
  onChange: (patch: Partial<FinancialRecordDraft>) => void;
  onSave: () => void;
};

function PanelBody({
  record,
  isLoading,
  loadError,
  isProcessing,
  isEditing,
  isSaving,
  saveError,
  draft,
  onCancel,
  onChange,
  onSave,
}: PanelBodyProps) {
  if (isLoading) {
    return (
      <Typography.Paragraph className="text-sm text-slate-500">
        Loading extracted data…
      </Typography.Paragraph>
    );
  }

  if (loadError) {
    return (
      <Typography.Paragraph className="text-sm text-rose-700">
        {loadError}
      </Typography.Paragraph>
    );
  }

  if (!record) {
    return (
      <Typography.Paragraph className="text-sm text-slate-500">
        {isProcessing
          ? "Structured fields will appear once extraction finishes."
          : "No structured data was extracted from this document."}
      </Typography.Paragraph>
    );
  }

  if (isEditing && draft) {
    return (
      <FinancialRecordForm
        draft={draft}
        isSaving={isSaving}
        saveError={saveError}
        onCancel={onCancel}
        onChange={onChange}
        onSave={onSave}
      />
    );
  }

  return <FinancialRecordSummary record={record} />;
}

function FinancialRecordSummary({ record }: { record: FinancialRecord }) {
  return (
    <Surface variant="transparent" className="space-y-3">
      <Surface
        variant="transparent"
        className="grid grid-cols-2 gap-2 sm:grid-cols-3"
      >
        <Detail label="Vendor" value={record.vendor ?? "—"} />
        <Detail label="Type" value={documentTypeLabel(record.document_type)} />
        <Detail label="Category" value={categoryLabel(record.category)} />
        <Detail
          label="Amount"
          value={formatCurrencyAmount(record.total_amount, record.currency)}
        />
        <Detail label="Currency" value={record.currency} />
        <Detail
          label="Payment"
          value={paymentStatusLabel(record.payment_status)}
        />
        <Detail
          label="Transaction date"
          value={formatRecordDate(record.transaction_date)}
        />
        <Detail label="Due date" value={formatRecordDate(record.due_date)} />
        <Detail
          label="Confidence"
          value={formatConfidence(record.confidence)}
        />
      </Surface>

      <Chip
        size="sm"
        variant="soft"
        color={record.extraction_method === "manual" ? "success" : "default"}
        className="rounded-md text-xs font-semibold"
      >
        {record.extraction_method === "manual"
          ? "Manually corrected"
          : "Auto-extracted (rules_v1)"}
      </Chip>
    </Surface>
  );
}

type FinancialRecordFormProps = {
  draft: FinancialRecordDraft;
  isSaving: boolean;
  saveError: string | null;
  onCancel: () => void;
  onChange: (patch: Partial<FinancialRecordDraft>) => void;
  onSave: () => void;
};

function FinancialRecordForm({
  draft,
  isSaving,
  saveError,
  onCancel,
  onChange,
  onSave,
}: FinancialRecordFormProps) {
  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSave();
      }}
      className="space-y-3"
    >
      <Surface
        variant="transparent"
        className="grid grid-cols-1 gap-3 sm:grid-cols-2"
      >
        <Field label="Vendor">
          <Input
            value={draft.vendor}
            onChange={(event) => onChange({ vendor: event.target.value })}
            className={FIELD_CLASS}
            disabled={isSaving}
          />
        </Field>

        <Field label="Type">
          <select
            value={draft.documentType}
            onChange={(event) =>
              onChange({
                documentType: event.target
                  .value as FinancialRecordDraft["documentType"],
              })
            }
            className={FIELD_CLASS}
            disabled={isSaving}
          >
            {DOCUMENT_TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Category">
          <select
            value={draft.category}
            onChange={(event) =>
              onChange({
                category: event.target
                  .value as FinancialRecordDraft["category"],
              })
            }
            className={FIELD_CLASS}
            disabled={isSaving}
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Payment status">
          <select
            value={draft.paymentStatus}
            onChange={(event) =>
              onChange({
                paymentStatus: event.target
                  .value as FinancialRecordDraft["paymentStatus"],
              })
            }
            className={FIELD_CLASS}
            disabled={isSaving}
          >
            {PAYMENT_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Total amount">
          <Input
            type="number"
            inputMode="decimal"
            step="0.01"
            min="0"
            value={draft.totalAmount}
            onChange={(event) => onChange({ totalAmount: event.target.value })}
            className={FIELD_CLASS}
            disabled={isSaving}
          />
        </Field>

        <Field label="Currency">
          <Input
            value={draft.currency}
            onChange={(event) => onChange({ currency: event.target.value })}
            className={FIELD_CLASS}
            disabled={isSaving}
          />
        </Field>

        <Field label="Transaction date">
          <Input
            type="date"
            value={draft.transactionDate}
            onChange={(event) =>
              onChange({ transactionDate: event.target.value })
            }
            className={FIELD_CLASS}
            disabled={isSaving}
          />
        </Field>

        <Field label="Due date">
          <Input
            type="date"
            value={draft.dueDate}
            onChange={(event) => onChange({ dueDate: event.target.value })}
            className={FIELD_CLASS}
            disabled={isSaving}
          />
        </Field>
      </Surface>

      {saveError ? (
        <Typography.Paragraph className="text-sm text-rose-700">
          {saveError}
        </Typography.Paragraph>
      ) : null}

      <Surface variant="transparent" className="flex gap-2">
        <Button
          type="submit"
          variant="primary"
          isDisabled={isSaving}
          className="min-h-10 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-600"
        >
          {isSaving ? "Saving" : "Save changes"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onPress={onCancel}
          isDisabled={isSaving}
          className="min-h-10 rounded-md border border-slate-200 px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-indigo-600"
        >
          Cancel
        </Button>
      </Surface>
    </form>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <Typography.Paragraph className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
        {label}
      </Typography.Paragraph>
      {children}
    </label>
  );
}
