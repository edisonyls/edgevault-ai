import { SummaryTile } from "@/components/ui/summary-tile";

type WorkspaceHeaderProps = {
  documentCount: number;
  readyCount: number;
  reviewCount: number;
};

export function WorkspaceHeader({
  documentCount,
  readyCount,
  reviewCount,
}: WorkspaceHeaderProps) {
  return (
    <header className="border-b border-slate-200 bg-white px-5 py-5 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold text-indigo-700">
            Bills, receipts, invoices
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-normal text-slate-950 sm:text-4xl">
            Review uploaded documents and ask questions about them.
          </h1>
          <p className="mt-3 text-base leading-7 text-slate-600">
            Manage file names, remove duplicates, and keep finance documents
            ready for AI-assisted lookup.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3 sm:min-w-[420px]">
          <SummaryTile label="Files" value={documentCount} />
          <SummaryTile label="Ready" value={readyCount} />
          <SummaryTile label="Review" value={reviewCount} tone="amber" />
        </div>
      </div>
    </header>
  );
}
