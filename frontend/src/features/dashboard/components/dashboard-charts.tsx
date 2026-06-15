"use client";

import { useMemo } from "react";
import {
  ArcElement,
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  type ChartConfiguration,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  DoughnutController,
  PointElement,
  Tooltip,
  type TooltipItem,
} from "chart.js";
import {
  categoryLabel,
  formatCurrencyAmount,
} from "@/features/documents/lib/financial-display";
import type {
  CategoryTotal,
  MonthlyTotal,
  VendorTotal,
} from "../lib/analytics";
import { useChart } from "./use-chart";

// Register only the controllers/elements actually used, once per module load.
Chart.register(
  ArcElement,
  BarController,
  BarElement,
  CategoryScale,
  DoughnutController,
  Filler,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
);

// A calm, distinguishable palette that sits next to the indigo brand accent.
const PALETTE = [
  "#4f46e5",
  "#0ea5e9",
  "#10b981",
  "#f59e0b",
  "#ec4899",
  "#8b5cf6",
  "#94a3b8",
];

Chart.defaults.font.family =
  "Inter, ui-sans-serif, system-ui, -apple-system, sans-serif";
Chart.defaults.color = "#475569";

function money(value: number, currency: string): string {
  return formatCurrencyAmount(value, currency);
}

export function CategoryDoughnut({
  data,
  currency,
}: {
  data: CategoryTotal[];
  currency: string;
}) {
  const config = useMemo<ChartConfiguration<"doughnut">>(
    () => ({
      type: "doughnut",
      data: {
        labels: data.map((entry) => categoryLabel(entry.category)),
        datasets: [
          {
            data: data.map((entry) => entry.total),
            backgroundColor: data.map(
              (_, index) => PALETTE[index % PALETTE.length],
            ),
            borderColor: "#ffffff",
            borderWidth: 2,
            hoverOffset: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: {
            position: "right",
            labels: {
              boxWidth: 12,
              boxHeight: 12,
              padding: 14,
              usePointStyle: true,
            },
          },
          tooltip: {
            callbacks: {
              label: (item: TooltipItem<"doughnut">) =>
                ` ${money(item.parsed, currency)}`,
            },
          },
        },
      },
    }),
    [data, currency],
  );

  return <canvas ref={useChart(config)} />;
}

export function VendorBar({
  data,
  currency,
}: {
  data: VendorTotal[];
  currency: string;
}) {
  const config = useMemo<ChartConfiguration<"bar">>(
    () => ({
      type: "bar",
      data: {
        labels: data.map((entry) => entry.vendor),
        datasets: [
          {
            data: data.map((entry) => entry.total),
            backgroundColor: "#4f46e5",
            borderRadius: 6,
            maxBarThickness: 26,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (item: TooltipItem<"bar">) =>
                ` ${money(item.parsed.x ?? 0, currency)}`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: "#f1f5f9" },
            ticks: {
              callback: (value) => money(Number(value), currency),
            },
          },
          y: { grid: { display: false } },
        },
      },
    }),
    [data, currency],
  );

  return <canvas ref={useChart(config)} />;
}

export function MonthlyTrendLine({
  data,
  currency,
}: {
  data: MonthlyTotal[];
  currency: string;
}) {
  const config = useMemo<ChartConfiguration<"line">>(
    () => ({
      type: "line",
      data: {
        labels: data.map((entry) => entry.label),
        datasets: [
          {
            data: data.map((entry) => entry.total),
            borderColor: "#4f46e5",
            backgroundColor: "rgba(79, 70, 229, 0.12)",
            fill: true,
            tension: 0.35,
            pointBackgroundColor: "#4f46e5",
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (item: TooltipItem<"line">) =>
                ` ${money(item.parsed.y ?? 0, currency)}`,
            },
          },
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            grid: { color: "#f1f5f9" },
            ticks: {
              callback: (value) => money(Number(value), currency),
            },
          },
        },
      },
    }),
    [data, currency],
  );

  return <canvas ref={useChart(config)} />;
}
