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
    <div
      className={`rounded-lg border bg-white p-4 ${
        tone === "amber" ? "border-amber-200" : "border-slate-200"
      }`}
    >
      <p className="text-2xl font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{label}</p>
    </div>
  );
}

export function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-2xl font-semibold text-slate-950">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{label}</p>
    </div>
  );
}
