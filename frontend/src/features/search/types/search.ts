import type {
  FinancialCategory,
  FinancialDocumentType,
  FinancialRecord,
} from "@/features/documents/types/financial-record";
import type { UploadMetadataResponse } from "@/features/documents/types/upload";

export type SearchResult = {
  upload: UploadMetadataResponse;
  financial_record: FinancialRecord | null;
  snippet: string | null;
  rank: number | null;
};

export type SearchMode = "keyword" | "semantic" | "hybrid";

export type SearchFilters = {
  q: string;
  mode: SearchMode;
  category: FinancialCategory | "all";
  documentType: FinancialDocumentType | "all";
  vendor: string;
  from: string;
  to: string;
};

export const EMPTY_SEARCH_FILTERS: SearchFilters = {
  q: "",
  mode: "keyword",
  category: "all",
  documentType: "all",
  vendor: "",
  from: "",
  to: "",
};
