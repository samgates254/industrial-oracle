import type { FreshnessState } from "@/design-system/tokens";

export function formatNumber(value: number, precision = 1): string {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  });
}

export function formatSigned(value: number, precision = 1, unit = ""): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  const abs = formatNumber(Math.abs(value), precision);
  return `${sign}${abs}${unit ? ` ${unit}` : ""}`;
}

export function formatTimestamp(iso: string, timeZone = "Africa/Nairobi"): string {
  const date = new Date(iso);
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone,
    timeZoneName: "short",
  }).format(date);
}

export function formatDateTime(iso: string, timeZone = "Africa/Nairobi"): string {
  const date = new Date(iso);
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone,
  }).format(date);
}

export function classifyFreshness(
  observedAt: string,
  nowIso: string,
  liveMs = 15_000,
  staleMs = 120_000,
): FreshnessState {
  const observed = Date.parse(observedAt);
  const now = Date.parse(nowIso);
  if (!Number.isFinite(observed) || !Number.isFinite(now)) return "offline";
  const age = now - observed;
  if (age < 0) return "updated";
  if (age <= liveMs) return "live";
  if (age <= staleMs) return "updated";
  return "stale";
}

export function formatAge(observedAt: string, nowIso: string): string {
  const age = Date.parse(nowIso) - Date.parse(observedAt);
  if (!Number.isFinite(age) || age < 0) return "—";
  if (age < 1000) return `${age} ms ago`;
  if (age < 60_000) return `${Math.round(age / 1000)}s ago`;
  const minutes = Math.floor(age / 60_000);
  const seconds = Math.floor((age % 60_000) / 1000);
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

export function moneyOrUnavailable(value: number | null, note: string): string {
  if (value === null) return note;
  return value.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}
