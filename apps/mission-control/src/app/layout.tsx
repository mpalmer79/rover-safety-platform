import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";
import { SiteNav } from "@/components/SiteNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mission Control · Rover Safety Platform",
  description:
    "Simulation-only mission control UI for the deterministic autonomy " +
    "validation and safety orchestration platform.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="console-backdrop min-h-dvh bg-base-0 text-base-800">
        <SafetyBoundaryBanner />
        <div className="grid min-h-[calc(100dvh-2.5rem)] grid-cols-[14rem_1fr]">
          <SiteNav />
          <main className="overflow-y-auto px-6 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
