"use client";

import { Link } from "@heroui/react";
import {
  FileText,
  LayoutDashboard,
  MessageSquare,
  Search,
  Tags,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { usePathname } from "next/navigation";

type TabItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

const tabs: TabItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Documents", href: "/", icon: FileText },
  { label: "Search", href: "/search", icon: Search },
  { label: "AI chat", href: "/chat", icon: MessageSquare },
  { label: "Vendors", href: "/vendors", icon: Tags },
];

export function MobileTabBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden"
    >
      <ul className="mx-auto flex max-w-[1600px] items-stretch justify-around">
        {tabs.map((tab) => {
          const isCurrent =
            tab.href === "/" ? pathname === "/" : pathname.startsWith(tab.href);
          const Icon = tab.icon;

          return (
            <li key={tab.href} className="flex-1">
              <Link
                href={tab.href}
                aria-current={isCurrent ? "page" : undefined}
                className={`flex min-h-14 flex-col items-center justify-center gap-1 px-2 py-2 text-[11px] font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 ${
                  isCurrent
                    ? "text-indigo-700"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                <Icon
                  aria-hidden="true"
                  className={`size-5 ${isCurrent ? "text-indigo-700" : "text-slate-400"}`}
                />
                {tab.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
