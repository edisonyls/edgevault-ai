import type {
  FinancialCategory,
  FinancialRecord,
} from "@/features/documents/types/financial-record";

export type CategoryTotal = {
  category: FinancialCategory;
  total: number;
};

export type VendorTotal = {
  vendor: string;
  total: number;
};

export type MonthlyTotal = {
  monthStart: Date;
  label: string;
  total: number;
};

export type DashboardAnalytics = {
  currency: string;
  recordCount: number;
  thisMonthTotal: number;
  lastMonthTotal: number;
  monthOverMonthChange: number | null;
  thisMonthBillCount: number;
  unpaidTotal: number;
  byCategory: CategoryTotal[];
  byVendor: VendorTotal[];
  monthlyTrend: MonthlyTotal[];
  recentRecords: FinancialRecord[];
  upcomingDueDates: FinancialRecord[];
};

const MONTHS_OF_TREND = 6;
const MAX_VENDORS = 6;
const MAX_RECENT = 6;
const MAX_UPCOMING = 6;

function parseDate(value: string | null): Date | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function isSameMonth(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth();
}

function monthLabel(date: Date): string {
  return date.toLocaleDateString(undefined, {
    month: "short",
    year: "2-digit",
  });
}

// Picks the currency that appears most often so the aggregate totals share a
// single symbol. Records mixing currencies are uncommon for a personal vault.
function dominantCurrency(records: FinancialRecord[]): string {
  const counts = new Map<string, number>();

  for (const record of records) {
    const currency = record.currency?.toUpperCase();
    if (currency) {
      counts.set(currency, (counts.get(currency) ?? 0) + 1);
    }
  }

  let best = "AUD";
  let bestCount = 0;
  for (const [currency, count] of counts) {
    if (count > bestCount) {
      best = currency;
      bestCount = count;
    }
  }

  return best;
}

export function computeDashboardAnalytics(
  records: FinancialRecord[],
  now: Date = new Date(),
): DashboardAnalytics {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const thisMonth = startOfMonth(today);
  const lastMonth = new Date(
    thisMonth.getFullYear(),
    thisMonth.getMonth() - 1,
    1,
  );

  // Build the trailing-6-month buckets, oldest first, all initialised to zero
  // so months with no spending still render a point on the trend line.
  const trendBuckets: MonthlyTotal[] = [];
  for (let offset = MONTHS_OF_TREND - 1; offset >= 0; offset -= 1) {
    const monthStart = new Date(
      thisMonth.getFullYear(),
      thisMonth.getMonth() - offset,
      1,
    );
    trendBuckets.push({ monthStart, label: monthLabel(monthStart), total: 0 });
  }

  const categoryTotals = new Map<FinancialCategory, number>();
  const vendorTotals = new Map<string, number>();

  let thisMonthTotal = 0;
  let lastMonthTotal = 0;
  let thisMonthBillCount = 0;
  let unpaidTotal = 0;

  for (const record of records) {
    const amount = record.total_amount ?? 0;
    const txnDate = parseDate(record.transaction_date);

    if (amount > 0) {
      const category = record.category ?? "other";
      categoryTotals.set(
        category,
        (categoryTotals.get(category) ?? 0) + amount,
      );

      if (record.vendor) {
        vendorTotals.set(
          record.vendor,
          (vendorTotals.get(record.vendor) ?? 0) + amount,
        );
      }
    }

    if (txnDate) {
      if (isSameMonth(txnDate, thisMonth)) {
        thisMonthTotal += amount;
        thisMonthBillCount += 1;
      } else if (isSameMonth(txnDate, lastMonth)) {
        lastMonthTotal += amount;
      }

      const bucket = trendBuckets.find((entry) =>
        isSameMonth(entry.monthStart, txnDate),
      );
      if (bucket) {
        bucket.total += amount;
      }
    }

    if (record.payment_status === "unpaid") {
      unpaidTotal += amount;
    }
  }

  const byCategory: CategoryTotal[] = [...categoryTotals.entries()]
    .map(([category, total]) => ({ category, total }))
    .sort((a, b) => b.total - a.total);

  const sortedVendors = [...vendorTotals.entries()]
    .map(([vendor, total]) => ({ vendor, total }))
    .sort((a, b) => b.total - a.total);

  // Keep the biggest spenders individually and fold the long tail into "Other".
  const byVendor: VendorTotal[] = sortedVendors.slice(0, MAX_VENDORS);
  const tailTotal = sortedVendors
    .slice(MAX_VENDORS)
    .reduce((sum, entry) => sum + entry.total, 0);
  if (tailTotal > 0) {
    byVendor.push({ vendor: "Other", total: tailTotal });
  }

  const recentRecords = [...records]
    .filter((record) => record.transaction_date)
    .sort((a, b) =>
      (b.transaction_date ?? "").localeCompare(a.transaction_date ?? ""),
    )
    .slice(0, MAX_RECENT);

  const upcomingDueDates = records
    .filter((record) => {
      const dueDate = parseDate(record.due_date);
      return (
        dueDate !== null && dueDate >= today && record.payment_status !== "paid"
      );
    })
    .sort((a, b) => (a.due_date ?? "").localeCompare(b.due_date ?? ""))
    .slice(0, MAX_UPCOMING);

  const monthOverMonthChange =
    lastMonthTotal > 0
      ? (thisMonthTotal - lastMonthTotal) / lastMonthTotal
      : null;

  return {
    currency: dominantCurrency(records),
    recordCount: records.length,
    thisMonthTotal,
    lastMonthTotal,
    monthOverMonthChange,
    thisMonthBillCount,
    unpaidTotal,
    byCategory,
    byVendor,
    monthlyTrend: trendBuckets,
    recentRecords,
    upcomingDueDates,
  };
}

// Whole days from today until the given due date string (negative = overdue).
export function daysUntil(
  dueDate: string | null,
  now: Date = new Date(),
): number | null {
  const parsed = parseDate(dueDate);
  if (!parsed) {
    return null;
  }

  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const msPerDay = 24 * 60 * 60 * 1000;
  return Math.round((parsed.getTime() - today.getTime()) / msPerDay);
}
