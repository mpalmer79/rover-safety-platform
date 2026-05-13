"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Layers,
  PlayCircle,
  ShieldCheck,
  Folder,
} from "lucide-react";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/start", label: "Start Here", icon: Activity },
  { href: "/demo/warehouse-replay", label: "Mission Replay Demo", icon: PlayCircle },
  { href: "/safety", label: "Safety Authority", icon: ShieldCheck },
  { href: "/evidence", label: "Evidence & Audit", icon: Folder },
  { href: "/workbench", label: "Proposal Workbench", icon: Layers },
] as const;

export function SiteNav() {
  const pathname = usePathname();
  return (
    <nav className="border-r border-base-200 bg-base-50 px-3 py-4">
      <Link href="/start" className="mb-4 block">
        <p className="label">ProjectBoundary</p>
        <p className="font-semibold leading-tight text-base-900">Mission Control</p>
      </Link>
      <ul className="space-y-1 text-sm">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active =
            pathname === href ||
            (href.length > 1 && pathname.startsWith(href));
          return (
            <li key={href}>
              <Link
                href={href}
                className={cn(
                  "flex items-center gap-2 rounded px-2 py-1.5 transition-colors",
                  active
                    ? "bg-base-100 text-base-900"
                    : "text-base-700 hover:bg-base-100",
                )}
              >
                <Icon aria-hidden className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-6 rounded border border-base-200 bg-base-100 px-3 py-3 text-[11px] leading-snug text-base-600">
        <p className="label mb-1">Scope</p>
        Simulation-only platform. Deterministic mission validation,
        supervisor authority, replay evidence, and audit traceability.
        No real hardware control. Not safety-certified.
      </div>
    </nav>
  );
}
