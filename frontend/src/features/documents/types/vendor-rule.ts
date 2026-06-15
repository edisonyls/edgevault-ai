import type { FinancialCategory } from "./financial-record";

export type VendorRule = {
  id: string;
  keyword: string;
  vendor: string;
  category: FinancialCategory;
  created_at: string;
  updated_at: string;
};

export type VendorRuleCreate = {
  keyword: string;
  vendor: string;
  category: FinancialCategory;
};

export type VendorRuleUpdate = {
  keyword?: string;
  vendor?: string;
  category?: FinancialCategory;
};
