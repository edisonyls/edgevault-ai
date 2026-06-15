import type {
  FinancialCategory,
  FinancialDocumentType,
  PaymentStatus,
} from "../api/financial-records";

export const DOCUMENT_TYPE_OPTIONS: {
  value: FinancialDocumentType;
  label: string;
}[] = [
  { value: "receipt", label: "Receipt" },
  { value: "invoice", label: "Invoice" },
  { value: "bill", label: "Bill" },
  { value: "statement", label: "Statement" },
  { value: "other", label: "Other" },
];

export const CATEGORY_OPTIONS: { value: FinancialCategory; label: string }[] = [
  { value: "groceries", label: "Groceries" },
  { value: "utilities", label: "Utilities" },
  { value: "internet_phone", label: "Internet / Phone" },
  { value: "transport", label: "Transport" },
  { value: "subscription", label: "Subscription" },
  { value: "other", label: "Other" },
];

export const PAYMENT_STATUS_OPTIONS: { value: PaymentStatus; label: string }[] =
  [
    { value: "paid", label: "Paid" },
    { value: "unpaid", label: "Unpaid" },
    { value: "unknown", label: "Unknown" },
  ];

export function documentTypeLabel(value: FinancialDocumentType | null): string {
  return (
    DOCUMENT_TYPE_OPTIONS.find((option) => option.value === value)?.label ?? "—"
  );
}

export function categoryLabel(value: FinancialCategory | null): string {
  return (
    CATEGORY_OPTIONS.find((option) => option.value === value)?.label ?? "—"
  );
}

export function paymentStatusLabel(value: PaymentStatus | null): string {
  return (
    PAYMENT_STATUS_OPTIONS.find((option) => option.value === value)?.label ??
    "—"
  );
}

const DOLLAR_CURRENCIES = new Set(["AUD", "USD", "NZD", "CAD", "SGD"]);

export function formatCurrencyAmount(
  amount: number | null,
  currency: string,
): string {
  if (amount === null) {
    return "—";
  }

  const normalizedCurrency = currency.toUpperCase();
  const formatted = amount.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  if (DOLLAR_CURRENCIES.has(normalizedCurrency)) {
    return `$${formatted}`;
  }

  return `${normalizedCurrency} ${formatted}`;
}

export function formatRecordDate(value: string | null): string {
  if (!value) {
    return "—";
  }

  const parsed = new Date(`${value}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatConfidence(confidence: number | null): string {
  if (confidence === null) {
    return "—";
  }

  return `${Math.round(confidence * 100)}%`;
}
