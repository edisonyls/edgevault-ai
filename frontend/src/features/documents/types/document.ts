export type DocumentStatus = "Ready" | "Review" | "Processing";

export type DocumentType = "Bill" | "Receipt" | "Invoice" | "Statement";

export type VaultDocument = {
  id: number;
  name: string;
  type: DocumentType;
  vendor: string;
  uploadedAt: string;
  size: string;
  amount: string;
  status: DocumentStatus;
};
