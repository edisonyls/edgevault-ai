import type { VaultDocument } from "../types/document";

export const initialDocuments: VaultDocument[] = [
  {
    id: "sample-1",
    name: "Electricity bill - May 2026.pdf",
    type: "Bill",
    vendor: "United Energy",
    uploadedAt: "Today, 9:24 AM",
    size: "1.8 MB",
    amount: "$184.30",
    status: "Ready",
  },
  {
    id: "sample-2",
    name: "Office supplies receipt.pdf",
    type: "Receipt",
    vendor: "Officeworks",
    uploadedAt: "Yesterday, 4:12 PM",
    size: "846 KB",
    amount: "$72.40",
    status: "Review",
  },
  {
    id: "sample-3",
    name: "Internet invoice - June.pdf",
    type: "Invoice",
    vendor: "Aussie Broadband",
    uploadedAt: "Jun 8, 2026",
    size: "2.1 MB",
    amount: "$99.00",
    status: "Ready",
  },
  {
    id: "sample-4",
    name: "Business account statement.csv",
    type: "Statement",
    vendor: "Bank export",
    uploadedAt: "Jun 5, 2026",
    size: "312 KB",
    amount: "$4,281.92",
    status: "Processing",
  },
];
