"use client";

import { Button, Link, Separator, Surface, Typography } from "@heroui/react";
import { LogOut } from "lucide-react";
import { usePathname } from "next/navigation";
import { workspaceNavigation } from "@/config/navigation";
import { Metric } from "@/components/ui/summary-tile";
import { MobileTabBar } from "@/components/layout/mobile-tab-bar";
import { useAuth } from "@/features/auth/components/auth-gate";

type AppSidebarProps = {
  documentCount: number;
  readyCount: number;
  failedCount: number;
  onPickFiles: () => void;
  isUploading: boolean;
  uploadError: string | null;
};

export function AppSidebar({
  documentCount,
  readyCount,
  failedCount,
  onPickFiles,
  isUploading,
  uploadError,
}: AppSidebarProps) {
  const pathname = usePathname();
  const { session, signOut } = useAuth();

  return (
    <>
    <Surface
      render={(props) => <aside {...props} />}
      className="sticky top-0 z-30 border-b border-slate-200 bg-white px-5 py-4 lg:static lg:w-64 lg:border-b-0 lg:border-r lg:px-6 lg:py-6"
    >
      <Surface
        variant="transparent"
        className="flex items-center justify-between gap-4 lg:block"
      >
        <Surface variant="transparent" className="flex items-center gap-3">
          <Surface
            variant="transparent"
            className="grid size-10 shrink-0 place-items-center rounded-md bg-slate-950 text-sm font-bold tracking-tight text-white"
          >
            EV
          </Surface>
          <Surface variant="transparent">
            <Typography.Paragraph className="text-base font-semibold">
              EdgeVault AI
            </Typography.Paragraph>
            <Typography.Paragraph className="text-sm text-slate-500">
              {session.workspace?.display_name ?? "Workspace"}
            </Typography.Paragraph>
          </Surface>
        </Surface>

        <Surface
          variant="transparent"
          className="flex items-center gap-2 lg:mt-8 lg:block"
        >
          <Button
            type="button"
            variant="primary"
            className="min-h-11 rounded-md bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 focus-visible:ring-2 focus-visible:ring-indigo-600 focus-visible:ring-offset-2 lg:w-full"
            onPress={onPickFiles}
            isDisabled={isUploading}
          >
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
          <Button
            type="button"
            variant="secondary"
            aria-label="Sign out"
            className="min-h-11 rounded-md border border-slate-200 bg-white px-3 text-slate-600 transition hover:bg-slate-100 hover:text-slate-950 lg:mt-2 lg:w-full"
            onPress={() => void signOut()}
          >
            <LogOut aria-hidden="true" className="size-4" />
            <span className="hidden lg:inline">Sign out</span>
          </Button>
        </Surface>
        {uploadError && (
          <Typography.Paragraph
            role="alert"
            className="mt-3 max-w-full text-sm text-rose-700 lg:text-xs"
          >
            {uploadError}
          </Typography.Paragraph>
        )}
      </Surface>

      <nav className="mt-5 hidden space-y-1 lg:block" aria-label="Workspace">
        {workspaceNavigation.map((item) => {
          const isCurrent =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const itemClassName = `flex min-h-11 w-full items-center rounded-md px-3 text-left text-sm font-medium transition focus:ring-2 focus:ring-indigo-600 ${
            isCurrent
              ? "bg-slate-950 text-white"
              : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
          }`;

          return (
            <Link
              key={item.label}
              href={item.href}
              className={itemClassName}
              aria-current={isCurrent ? "page" : undefined}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <Surface variant="transparent" className="mt-6 hidden lg:block">
        <Separator className="mb-6 bg-slate-200" />
        <Typography.Paragraph className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
          This month
        </Typography.Paragraph>
        <Surface variant="transparent" className="mt-4 space-y-4">
          <Metric label="Uploaded" value={String(documentCount)} />
          <Metric label="Ready to query" value={String(readyCount)} />
          <Metric label="Failed" value={String(failedCount)} />
        </Surface>
      </Surface>
    </Surface>

    <MobileTabBar />
    </>
  );
}
