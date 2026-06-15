import type { VaultDocument } from "../types/document";

export function typeColor(type: VaultDocument["type"]) {
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

export function statusColor(status: VaultDocument["status"]) {
  switch (status) {
    case "Ready":
      return "success";
    case "Processing":
      return "accent";
    case "Indexing":
      return "warning";
    case "Failed":
      return "danger";
  }
}
