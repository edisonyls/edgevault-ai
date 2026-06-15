const apiBaseUrl = process.env
  .NEXT_PUBLIC_API_BASE_URL!.trim()
  .replace(/\/$/, "");

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

export async function listFinancialRecords(
  options: { signal?: AbortSignal } = {},
): Promise<FinancialRecord[]> {
  const response = await fetch(`${apiBaseUrl}/financial-records`, {
    method: "GET",
    signal: options.signal,
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<FinancialRecord[]>;
}

/**
 * Fetches the structured record for one document. Returns null when extraction
 * has not produced a record yet.
 */
export async function getFinancialRecord(
  uploadId: string,
  options: { signal?: AbortSignal } = {},
): Promise<FinancialRecord | null> {
  const response = await fetch(
    `${apiBaseUrl}/uploads/${uploadId}/financial-record`,
    {
      method: "GET",
      signal: options.signal,
    },
  );

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Load failed"));
  }

  return response.json() as Promise<FinancialRecord>;
}

export async function updateFinancialRecord(
  id: string,
  update: FinancialRecordUpdate,
): Promise<FinancialRecord> {
  const response = await fetch(`${apiBaseUrl}/financial-records/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Update failed"));
  }

  return response.json() as Promise<FinancialRecord>;
}

async function getErrorMessage(response: Response, fallback: string) {
  try {
    const payload = (await response.json()) as { detail?: unknown };

    if (typeof payload.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Fall through to the generic status message.
  }

  return `${fallback} with status ${response.status}.`;
}
