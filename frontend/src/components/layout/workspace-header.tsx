import { Surface, Typography } from "@heroui/react";
import { SummaryTile } from "@/components/ui/summary-tile";

type WorkspaceHeaderProps = {
  documentCount: number;
  readyCount: number;
  failedCount: number;
};

export function WorkspaceHeader({
  documentCount,
  readyCount,
  failedCount,
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
            className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl"
          >
            Your documents
          </Typography.Heading>
          <Typography.Paragraph className="mt-2 text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
            Review uploaded files, tidy up names and duplicates, and ask
            questions about them with AI-assisted lookup.
          </Typography.Paragraph>
        </Surface>

        <Surface
          variant="transparent"
          className="grid grid-cols-3 gap-3 sm:min-w-[420px]"
        >
          <SummaryTile label="Files" value={documentCount} />
          <SummaryTile label="Ready" value={readyCount} />
          <SummaryTile label="Failed" value={failedCount} tone="amber" />
        </Surface>
      </Surface>
    </Surface>
  );
}
