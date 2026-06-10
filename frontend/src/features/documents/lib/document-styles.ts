import type { DocumentStatus, DocumentType } from "../types/document";

export const statusStyles: Record<DocumentStatus, string> = {
  Ready: "border-emerald-200 bg-emerald-50 text-emerald-700",
  Review: "border-amber-200 bg-amber-50 text-amber-800",
  Processing: "border-sky-200 bg-sky-50 text-sky-700",
};

export const typeStyles: Record<DocumentType, string> = {
  Bill: "bg-indigo-50 text-indigo-700",
  Receipt: "bg-teal-50 text-teal-700",
  Invoice: "bg-slate-100 text-slate-700",
  Statement: "bg-rose-50 text-rose-700",
};
