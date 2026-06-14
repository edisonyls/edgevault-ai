import type { UploadMetadataResponse } from "../api/uploads";
import type {
  DocumentStatus,
  DocumentType,
  VaultDocument,
} from "../types/document";

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

export function formatUploadedAt(timestamp: string) {
  const uploadedAt = new Date(timestamp);

  if (Number.isNaN(uploadedAt.getTime())) {
    return "Just now";
  }

  const now = new Date();
  const elapsedMs = now.getTime() - uploadedAt.getTime();

  if (elapsedMs >= 0 && elapsedMs < 60 * 1000) {
    return "Just now";
  }

  const timeFormatter = new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
  const dateFormatter = new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  if (uploadedAt.toDateString() === now.toDateString()) {
    return `Today, ${timeFormatter.format(uploadedAt)}`;
  }

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);

  if (uploadedAt.toDateString() === yesterday.toDateString()) {
    return `Yesterday, ${timeFormatter.format(uploadedAt)}`;
  }

  return dateFormatter.format(uploadedAt);
}

export function mapUploadToDocument(
  upload: UploadMetadataResponse,
): VaultDocument {
  return {
    id: upload.id,
    name: upload.display_filename,
    type: inferDocumentType(upload.display_filename),
    vendor: "New upload",
    uploadedAt: formatUploadedAt(upload.created_at),
    size: formatFileSize(upload.file_size),
    amount: "Pending",
    status: mapUploadStatus(upload.status),
    text: upload.text,
  };
}

export function sumDetectedAmounts(documents: VaultDocument[]) {
  return documents
    .filter((document) => document.amount.startsWith("$"))
    .map((document) => Number(document.amount.replace(/[$,]/g, "")))
    .reduce((sum, value) => sum + value, 0);
}

function mapUploadStatus(status: string): DocumentStatus {
  switch (status.toLowerCase()) {
    case "processed":
      return "Ready";
    case "failed":
      return "Failed";
    case "uploaded":
    case "processing":
    default:
      return "Processing";
  }
}
