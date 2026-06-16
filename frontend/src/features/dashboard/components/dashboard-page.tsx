"use client";

import type { ChangeEvent, ReactNode } from "react";
import { useRef } from "react";
import { Card, Link, Surface, Typography } from "@heroui/react";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { useDocuments } from "@/features/documents/hooks/use-documents";
import {
  categoryLabel,
  documentTypeLabel,
  formatCurrencyAmount,
  formatRecordDate,
} from "@/features/documents/lib/financial-display";
import type { FinancialRecord } from "@/features/documents/types/financial-record";
import { useDashboard } from "../hooks/use-dashboard";
import { daysUntil } from "../lib/analytics";
import {
  CategoryDoughnut,
  MonthlyTrendLine,
  VendorBar,
} from "./dashboard-charts";

export function DashboardPage() {
  const { documents, isUploading, uploadError, uploadFiles } = useDocuments();
  const { analytics, isLoading, error, reload } = useDashboard();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const readyCount = documents.filter(
    (document) => document.status === "Ready",
  ).length;
  const failedCount = documents.filter(
    (document) => document.status === "Failed",
  ).length;

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    await uploadFiles(files);
  }

  const { currency } = analytics;
  const hasCategoryData = analytics.byCategory.length > 0;
  const hasVendorData = analytics.byVendor.length > 0;
  const hasTrendData = analytics.monthlyTrend.some((entry) => entry.total > 0);

  return (
    <Surface
      render={(props) => <main {...props} />}
      id="main-content"
      className="min-h-screen bg-[#f7f8fb] pb-20 text-slate-950 lg:pb-0"
    >
      <Link
        href="#dashboard"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-3 focus:text-sm focus:font-semibold focus:text-slate-950 focus:ring-2 focus:ring-indigo-600"
      >
        Skip to dashboard
      </Link>

      <Surface
        variant="transparent"
        className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col lg:flex-row"
      >
        <AppSidebar
          documentCount={documents.length}
          readyCount={readyCount}
          failedCount={failedCount}
          onPickFiles={openFilePicker}
          isUploading={isUploading}
          uploadError={uploadError}
        />

        <input
          ref={fileInputRef}
          className="sr-only"
          type="file"
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.csv,.doc,.docx"
          onChange={handleUpload}
          disabled={isUploading}
        />

        <Surface
          render={(props) => <section {...props} />}
          id="dashboard"
          variant="transparent"
          className="min-w-0 flex-1"
        >
          <Surface
            render={(props) => <header {...props} />}
            className="border-b border-slate-200 bg-white px-5 py-6 sm:px-6 lg:px-8"
          >
            <Typography.Paragraph className="text-sm font-semibold text-indigo-700">
              Spending overview
            </Typography.Paragraph>
            <Typography.Heading
              level={1}
              className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl"
            >
              Dashboard
            </Typography.Heading>
            <Typography.Paragraph className="mt-2 text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
              A snapshot of where your money goes, drawn from your uploaded
              receipts, invoices, and bills.
            </Typography.Paragraph>
          </Surface>

          <Surface
            variant="transparent"
            className="space-y-6 px-5 py-6 sm:px-6 lg:px-8"
          >
            {error && (
              <Card className="flex flex-col gap-2 rounded-lg border border-rose-200 bg-rose-50 p-4 sm:flex-row sm:items-center sm:justify-between">
                <Typography.Paragraph
                  role="alert"
                  className="text-sm text-rose-700"
                >
                  {error}
                </Typography.Paragraph>
                <button
                  type="button"
                  onClick={() => void reload()}
                  className="self-start rounded-md border border-rose-300 bg-white px-3 py-1.5 text-sm font-semibold text-rose-700 transition hover:bg-rose-100"
                >
                  Retry
                </button>
              </Card>
            )}

            <Surface
              variant="transparent"
              className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
            >
              <StatCard
                label="Spent this month"
                value={formatCurrencyAmount(analytics.thisMonthTotal, currency)}
                hint={
                  <MonthOverMonth change={analytics.monthOverMonthChange} />
                }
                isLoading={isLoading}
              />
              <StatCard
                label="Bills this month"
                value={String(analytics.thisMonthBillCount)}
                hint="Records dated this month"
                isLoading={isLoading}
              />
              <StatCard
                label="Outstanding (unpaid)"
                value={formatCurrencyAmount(analytics.unpaidTotal, currency)}
                hint="Across all records"
                tone={analytics.unpaidTotal > 0 ? "amber" : "slate"}
                isLoading={isLoading}
              />
              <StatCard
                label="Tracked records"
                value={String(analytics.recordCount)}
                hint="Total in your vault"
                isLoading={isLoading}
              />
            </Surface>

            <Surface
              variant="transparent"
              className="grid grid-cols-1 gap-6 xl:grid-cols-3"
            >
              <ChartCard
                title="Monthly trend"
                subtitle="Spending over the last 6 months"
                className="xl:col-span-2"
              >
                <ChartFrame
                  isLoading={isLoading}
                  isEmpty={!hasTrendData}
                  height="h-72"
                >
                  <MonthlyTrendLine
                    data={analytics.monthlyTrend}
                    currency={currency}
                  />
                </ChartFrame>
              </ChartCard>

              <ChartCard title="By category" subtitle="Where your money goes">
                <ChartFrame
                  isLoading={isLoading}
                  isEmpty={!hasCategoryData}
                  height="h-72"
                >
                  <CategoryDoughnut
                    data={analytics.byCategory}
                    currency={currency}
                  />
                </ChartFrame>
              </ChartCard>
            </Surface>

            <Surface
              variant="transparent"
              className="grid grid-cols-1 gap-6 xl:grid-cols-3"
            >
              <ChartCard
                title="Top vendors"
                subtitle="Highest total spend"
                className="xl:col-span-2"
              >
                <ChartFrame
                  isLoading={isLoading}
                  isEmpty={!hasVendorData}
                  height="h-72"
                >
                  <VendorBar data={analytics.byVendor} currency={currency} />
                </ChartFrame>
              </ChartCard>

              <ChartCard
                title="Upcoming due dates"
                subtitle="Unpaid bills coming up"
              >
                <UpcomingList
                  records={analytics.upcomingDueDates}
                  isLoading={isLoading}
                />
              </ChartCard>
            </Surface>

            <ChartCard
              title="Recent bills & receipts"
              subtitle="Your latest tracked documents"
            >
              <RecentList
                records={analytics.recentRecords}
                isLoading={isLoading}
              />
            </ChartCard>
          </Surface>
        </Surface>
      </Surface>
    </Surface>
  );
}

function StatCard({
  label,
  value,
  hint,
  tone = "slate",
  isLoading,
}: {
  label: string;
  value: string;
  hint?: ReactNode;
  tone?: "slate" | "amber";
  isLoading: boolean;
}) {
  return (
    <Card
      className={`rounded-lg border bg-white p-5 ${
        tone === "amber" ? "border-amber-200" : "border-slate-200"
      }`}
    >
      <Typography.Paragraph className="text-sm text-slate-500">
        {label}
      </Typography.Paragraph>
      {isLoading ? (
        <div className="mt-2 h-8 w-28 animate-pulse rounded bg-slate-100" />
      ) : (
        <Typography.Paragraph className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
          {value}
        </Typography.Paragraph>
      )}
      {hint && !isLoading && (
        <div className="mt-1 text-xs text-slate-500">{hint}</div>
      )}
    </Card>
  );
}

function MonthOverMonth({ change }: { change: number | null }) {
  if (change === null) {
    return <span>No prior month to compare</span>;
  }

  const percent = Math.round(Math.abs(change) * 100);
  const isUp = change > 0;
  const tone = isUp ? "text-rose-600" : "text-emerald-600";
  const arrow = isUp ? "▲" : "▼";

  return (
    <span className={tone}>
      {arrow} {percent}% vs. last month
    </span>
  );
}

function ChartCard({
  title,
  subtitle,
  className = "",
  children,
}: {
  title: string;
  subtitle: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Card
      className={`rounded-lg border border-slate-200 bg-white p-5 ${className}`}
    >
      <Typography.Heading
        level={2}
        className="text-base font-semibold text-slate-950"
      >
        {title}
      </Typography.Heading>
      <Typography.Paragraph className="mt-0.5 text-sm text-slate-500">
        {subtitle}
      </Typography.Paragraph>
      <div className="mt-4">{children}</div>
    </Card>
  );
}

function ChartFrame({
  isLoading,
  isEmpty,
  height,
  children,
}: {
  isLoading: boolean;
  isEmpty: boolean;
  height: string;
  children: ReactNode;
}) {
  if (isLoading) {
    return (
      <div className={`${height} animate-pulse rounded-md bg-slate-100`} />
    );
  }

  if (isEmpty) {
    return (
      <div
        className={`${height} grid place-items-center rounded-md border border-dashed border-slate-200 text-sm text-slate-400`}
      >
        No data yet
      </div>
    );
  }

  return <div className={`relative ${height}`}>{children}</div>;
}

function UpcomingList({
  records,
  isLoading,
}: {
  records: FinancialRecord[];
  isLoading: boolean;
}) {
  if (isLoading) {
    return <ListSkeleton rows={4} />;
  }

  if (records.length === 0) {
    return (
      <Typography.Paragraph className="py-8 text-center text-sm text-slate-400">
        Nothing due — you&apos;re all caught up.
      </Typography.Paragraph>
    );
  }

  return (
    <ul className="divide-y divide-slate-100">
      {records.map((record) => {
        const remaining = daysUntil(record.due_date);
        return (
          <li
            key={record.id}
            className="flex items-center justify-between gap-3 py-3"
          >
            <div className="min-w-0">
              <Typography.Paragraph className="truncate text-sm font-medium text-slate-950">
                {record.vendor ?? "Unknown vendor"}
              </Typography.Paragraph>
              <Typography.Paragraph className="text-xs text-slate-500">
                Due {formatRecordDate(record.due_date)}
                {remaining !== null && (
                  <span
                    className={
                      remaining <= 3 ? " text-rose-600" : " text-slate-500"
                    }
                  >
                    {" · "}
                    {remaining === 0
                      ? "today"
                      : remaining < 0
                        ? `${Math.abs(remaining)}d overdue`
                        : `in ${remaining}d`}
                  </span>
                )}
              </Typography.Paragraph>
            </div>
            <Typography.Paragraph className="shrink-0 text-sm font-semibold text-slate-950">
              {formatCurrencyAmount(record.total_amount, record.currency)}
            </Typography.Paragraph>
          </li>
        );
      })}
    </ul>
  );
}

function RecentList({
  records,
  isLoading,
}: {
  records: FinancialRecord[];
  isLoading: boolean;
}) {
  if (isLoading) {
    return <ListSkeleton rows={5} />;
  }

  if (records.length === 0) {
    return (
      <Typography.Paragraph className="py-8 text-center text-sm text-slate-400">
        Upload a receipt or invoice to see it here.
      </Typography.Paragraph>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <th className="py-2 pr-4 font-medium">Vendor</th>
            <th className="py-2 pr-4 font-medium">Type</th>
            <th className="py-2 pr-4 font-medium">Category</th>
            <th className="py-2 pr-4 font-medium">Date</th>
            <th className="py-2 pl-4 text-right font-medium">Amount</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {records.map((record) => (
            <tr key={record.id}>
              <td className="py-3 pr-4 font-medium text-slate-950">
                {record.vendor ?? "—"}
              </td>
              <td className="py-3 pr-4 text-slate-600">
                {documentTypeLabel(record.document_type)}
              </td>
              <td className="py-3 pr-4 text-slate-600">
                {categoryLabel(record.category)}
              </td>
              <td className="py-3 pr-4 text-slate-600">
                {formatRecordDate(record.transaction_date)}
              </td>
              <td className="py-3 pl-4 text-right font-semibold text-slate-950">
                {formatCurrencyAmount(record.total_amount, record.currency)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ListSkeleton({ rows }: { rows: number }) {
  return (
    <div className="space-y-3 py-2">
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="h-10 animate-pulse rounded-md bg-slate-100"
        />
      ))}
    </div>
  );
}
