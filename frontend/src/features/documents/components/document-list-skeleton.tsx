import { Skeleton, Surface } from "@heroui/react";

export function DocumentListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <Surface
      variant="transparent"
      aria-hidden="true"
      className="divide-y divide-slate-200"
    >
      {Array.from({ length: rows }).map((_, index) => (
        <Surface
          key={index}
          variant="transparent"
          className="flex items-center gap-3 px-4 py-4"
        >
          <Skeleton className="size-10 shrink-0 rounded-md" />
          <Surface variant="transparent" className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-4 w-2/5 rounded" />
            <Skeleton className="h-3 w-1/4 rounded" />
          </Surface>
          <Skeleton className="hidden h-4 w-20 rounded sm:block" />
          <Skeleton className="h-6 w-16 rounded-md" />
        </Surface>
      ))}
    </Surface>
  );
}
