import { Surface, Typography } from "@heroui/react";
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
    <Surface
      render={(props) => <header {...props} />}
      className="border-b border-slate-200 bg-white px-5 py-5 sm:px-6 lg:px-8"
    >
      <Surface
        variant="transparent"
        className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between"
      >
        <Surface variant="transparent" className="max-w-2xl">
          <Typography.Paragraph className="text-sm font-semibold text-indigo-700">
            Bills, receipts, invoices
          </Typography.Paragraph>
          <Typography.Heading
            level={1}
            className="mt-2 text-3xl font-semibold tracking-normal text-slate-950 sm:text-4xl"
          >
            Review uploaded documents and ask questions about them.
          </Typography.Heading>
          <Typography.Paragraph className="mt-3 text-base leading-7 text-slate-600">
            Manage file names, remove duplicates, and keep finance documents
            ready for AI-assisted lookup.
          </Typography.Paragraph>
        </Surface>

        <Surface
          variant="transparent"
          className="grid grid-cols-3 gap-3 sm:min-w-[420px]"
        >
          <SummaryTile label="Files" value={documentCount} />
          <SummaryTile label="Ready" value={readyCount} />
          <SummaryTile label="Review" value={reviewCount} tone="amber" />
        </Surface>
      </Surface>
    </Surface>
  );
}
