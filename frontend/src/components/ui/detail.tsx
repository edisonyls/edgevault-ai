import { Card, Typography } from "@heroui/react";

export function Detail({ label, value }: { label: string; value: string }) {
  return (
    <Card className="rounded-md bg-slate-50 p-3 shadow-none">
      <Typography.Paragraph className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">
        {label}
      </Typography.Paragraph>
      <Typography.Paragraph className="mt-1 break-words font-semibold text-slate-950">
        {value}
      </Typography.Paragraph>
    </Card>
  );
}
