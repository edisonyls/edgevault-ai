"use client";

import { useMemo } from "react";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartOptions,
  type TooltipItem,
} from "chart.js";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import {
  categoryLabel,
  formatCurrencyAmount,
} from "@/features/documents/lib/financial-display";
import type {
  CategoryTotal,
  MonthlyTotal,
  VendorTotal,
} from "../lib/analytics";

// Register only the controllers/elements actually used, once per module load.
ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
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

ChartJS.defaults.font.family =
  "Inter, ui-sans-serif, system-ui, -apple-system, sans-serif";
ChartJS.defaults.color = "#475569";

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
  const chartData = useMemo(
    () => ({
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
    }),
    [data],
  );

  const options = useMemo<ChartOptions<"doughnut">>(
    () => ({
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
    }),
    [currency],
  );

  return <Doughnut data={chartData} options={options} />;
}

export function VendorBar({
  data,
  currency,
}: {
  data: VendorTotal[];
  currency: string;
}) {
  const chartData = useMemo(
    () => ({
      labels: data.map((entry) => entry.vendor),
      datasets: [
        {
          data: data.map((entry) => entry.total),
          backgroundColor: "#4f46e5",
          borderRadius: 6,
          maxBarThickness: 26,
        },
      ],
    }),
    [data],
  );

  const options = useMemo<ChartOptions<"bar">>(
    () => ({
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
    }),
    [currency],
  );

  return <Bar data={chartData} options={options} />;
}

export function MonthlyTrendLine({
  data,
  currency,
}: {
  data: MonthlyTotal[];
  currency: string;
}) {
  const chartData = useMemo(
    () => ({
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
    }),
    [data],
  );

  const options = useMemo<ChartOptions<"line">>(
    () => ({
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
    }),
    [currency],
  );

  return <Line data={chartData} options={options} />;
}
