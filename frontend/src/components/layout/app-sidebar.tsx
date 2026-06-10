import type { ChangeEvent } from "react";
import { workspaceNavigation } from "@/config/navigation";
import { IconSpark, IconUpload } from "@/components/icons";
import { Metric } from "@/components/ui/summary-tile";

type AppSidebarProps = {
  documentCount: number;
  readyCount: number;
  reviewCount: number;
  onUpload: (event: ChangeEvent<HTMLInputElement>) => void;
};

export function AppSidebar({
  documentCount,
  readyCount,
  reviewCount,
  onUpload,
}: AppSidebarProps) {
  return (
    <aside className="border-b border-slate-200 bg-white px-5 py-4 lg:w-64 lg:border-b-0 lg:border-r lg:px-6 lg:py-6">
      <div className="flex items-center justify-between gap-4 lg:block">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-md bg-slate-950 text-white">
            <IconSpark className="size-5" />
          </div>
          <div>
            <p className="text-base font-semibold">EdgeVault AI</p>
            <p className="text-sm text-slate-500">Document workspace</p>
          </div>
        </div>

        <label className="inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-md bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus-within:ring-2 focus-within:ring-indigo-600 focus-within:ring-offset-2 lg:mt-8 lg:w-full">
          <IconUpload className="size-4" />
          Upload
          <input
            className="sr-only"
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.csv,.doc,.docx"
            onChange={onUpload}
          />
        </label>
      </div>

      <nav className="mt-5 hidden space-y-1 lg:block" aria-label="Workspace">
        {workspaceNavigation.map((item) => (
          <a
            key={item.label}
            href={item.href}
            className={`flex min-h-11 items-center rounded-md px-3 text-sm font-medium transition focus:ring-2 focus:ring-indigo-600 ${
              item.isActive
                ? "bg-slate-950 text-white"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
            }`}
          >
            {item.label}
          </a>
        ))}
      </nav>

      <div className="mt-6 hidden border-t border-slate-200 pt-6 lg:block">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
          This month
        </p>
        <div className="mt-4 space-y-4">
          <Metric label="Uploaded" value={String(documentCount)} />
          <Metric label="Ready to query" value={String(readyCount)} />
          <Metric label="Needs review" value={String(reviewCount)} />
        </div>
      </div>
    </aside>
  );
}
