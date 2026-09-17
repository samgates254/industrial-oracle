import { Radio, Clock, Hourglass, Unplug } from "lucide-react";
import type { FreshnessState } from "@/design-system/tokens";
import { formatAge, formatTimestamp } from "@/lib/format";
import { cn } from "@/lib/cn";

const copy: Record<
  FreshnessState,
  { label: string; icon: typeof Radio; className: string }
> = {
  live: { label: "Live", icon: Radio, className: "text-data-telemetry" },
  updated: { label: "Updated", icon: Clock, className: "text-secondary" },
  stale: { label: "Stale", icon: Hourglass, className: "text-state-warning" },
  offline: { label: "Offline", icon: Unplug, className: "text-state-offline" },
};

export function FreshnessIndicator({
  state,
  observedAt,
  nowIso,
  timeZone,
  className,
}: {
  state: FreshnessState;
  observedAt: string;
  nowIso?: string;
  timeZone?: string;
  className?: string;
}) {
  const item = copy[state];
  const Icon = item.icon;
  const ageMs =
    nowIso && Number.isFinite(Date.parse(nowIso)) && Number.isFinite(Date.parse(observedAt))
      ? Date.parse(nowIso) - Date.parse(observedAt)
      : null;
  const relative =
    nowIso && ageMs !== null && ageMs >= 1000 ? formatAge(observedAt, nowIso) : null;
  const detail =
    state === "offline"
      ? `Last received ${formatTimestamp(observedAt, timeZone)}`
      : relative ?? formatTimestamp(observedAt, timeZone);

  return (
    <span
      className={cn("inline-flex items-center gap-1.5 type-meta", item.className, className)}
      title={`${item.label} · ${formatTimestamp(observedAt, timeZone)}`}
    >
      <Icon aria-hidden className="h-3 w-3" strokeWidth={1.75} />
      <span className="type-status">{item.label}</span>
      <span className="type-timestamp text-muted">{detail}</span>
    </span>
  );
}
