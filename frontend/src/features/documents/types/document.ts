export type DocumentStatus =
  | "Ready"
  | "Processing"
  | "Extracting"
  | "Indexing"
  | "Failed";

export type DocumentType = "Bill" | "Receipt" | "Invoice" | "Statement";

export const DOCUMENT_TYPE_FILTERS = [
  "All",
  "Bill",
  "Receipt",
  "Invoice",
  "Statement",
] as const;

export type DocumentTypeFilter = (typeof DOCUMENT_TYPE_FILTERS)[number];

export type VaultDocument = {
  id: string;
  name: string;
  type: DocumentType;
  vendor: string;
  uploadedAt: string;
  size: string;
  amount: string;
  status: DocumentStatus;
  category: string | null;
  text: string | null;
};
