import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class strings; safe to compose freely in JSX. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Format an ISO-8601 timestamp deterministically (UTC, second precision). */
export function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toISOString().replace(/\.\d{3}Z$/, "Z");
  } catch {
    return iso;
  }
}

/** Truncate a deterministic hash for inline display. */
export function shortHash(hash: string | null | undefined, length = 12): string {
  if (!hash) return "—";
  return hash.length <= length ? hash : `${hash.slice(0, length)}…`;
}
