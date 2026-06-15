export type FinancialDocumentType =
  | "receipt"
  | "invoice"
  | "bill"
  | "statement"
  | "other";

export type FinancialCategory =
  | "groceries"
  | "utilities"
  | "internet_phone"
  | "transport"
  | "subscription"
  | "other";

export type PaymentStatus = "paid" | "unpaid" | "unknown";

export type ExtractionMethod = "rules_v1" | "manual";

export type FinancialRecord = {
  id: string;
  upload_id: string;
  document_type: FinancialDocumentType | null;
  vendor: string | null;
  transaction_date: string | null;
  due_date: string | null;
  total_amount: number | null;
  currency: string;
  category: FinancialCategory | null;
  payment_status: PaymentStatus | null;
  extraction_method: ExtractionMethod;
  confidence: number | null;
  created_at: string;
  updated_at: string;
};

export type FinancialRecordUpdate = {
  document_type?: FinancialDocumentType | null;
  vendor?: string | null;
  transaction_date?: string | null;
  due_date?: string | null;
  total_amount?: number | null;
  currency?: string;
  category?: FinancialCategory | null;
  payment_status?: PaymentStatus | null;
};
