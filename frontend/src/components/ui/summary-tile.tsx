import { Card, Surface, Typography } from "@heroui/react";

type SummaryTileProps = {
  label: string;
  value: number;
  tone?: "slate" | "amber";
};

export function SummaryTile({
  label,
  value,
  tone = "slate",
}: SummaryTileProps) {
  return (
    <Card
      className={`rounded-lg border bg-white p-4 ${
        tone === "amber" ? "border-amber-200" : "border-slate-200"
      }`}
    >
      <Typography.Paragraph className="text-2xl font-semibold text-slate-950">
        {value}
      </Typography.Paragraph>
      <Typography.Paragraph className="mt-1 text-sm text-slate-500">
        {label}
      </Typography.Paragraph>
    </Card>
  );
}

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Surface variant="transparent">
      <Typography.Paragraph className="text-2xl font-semibold text-slate-950">
        {value}
      </Typography.Paragraph>
      <Typography.Paragraph className="mt-1 text-sm text-slate-500">
        {label}
      </Typography.Paragraph>
    </Surface>
  );
}
