import type { DocumentType, VaultDocument } from "../types/document";

export function inferDocumentType(fileName: string): DocumentType {
  const normalizedName = fileName.toLowerCase();

  if (normalizedName.includes("receipt")) {
    return "Receipt";
  }

  if (normalizedName.includes("invoice")) {
    return "Invoice";
  }

  if (normalizedName.includes("statement") || normalizedName.endsWith(".csv")) {
    return "Statement";
  }

  return "Bill";
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }

  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function sumDetectedAmounts(documents: VaultDocument[]) {
  return documents
    .filter((document) => document.amount.startsWith("$"))
    .map((document) => Number(document.amount.replace(/[$,]/g, "")))
    .reduce((sum, value) => sum + value, 0);
}
