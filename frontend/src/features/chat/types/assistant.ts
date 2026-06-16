import type { FinancialCategory } from "@/features/documents/types/financial-record";

// Mirrors the backend's AssistantQueryType. "unknown" means no rule matched and
// the assistant returned a capability message instead of guessing.
export type AssistantQueryType =
  | "top_spending_category"
  | "category_total"
  | "vendor_total"
  | "vendor_list"
  | "document_count"
  | "unpaid_bills"
  | "subscriptions"
  | "spending_summary"
  | "unknown";

// A single financial record cited as evidence for an answer.
export type SupportingRecord = {
  upload_id: string;
  vendor: string | null;
  amount: number | null;
  date: string | null;
  category: FinancialCategory | null;
};

export type AssistantQueryResponse = {
  answer: string;
  query_type: AssistantQueryType;
  supporting_records: SupportingRecord[];
};
