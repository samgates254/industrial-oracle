import Link from "next/link";
import { Siren } from "lucide-react";
import type { Alert } from "@/types/operational";
import { formatTimestamp } from "@/lib/format";
import { cn } from "@/lib/cn";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const priorityTone = {
  P1: "critical",
  P2: "warning",
  P3: "neutral",
  P4: "neutral",
} as const;

export function AlertBanner({ alerts }: { alerts: Alert[] }) {
  const p1 = alerts.filter((a) => a.priority === "P1" && !a.acknowledged);
  const p2 = alerts.filter((a) => a.priority === "P2" && !a.acknowledged);
  if (p1.length === 0 && p2.length === 0) return null;

  const lead = p1[0] ?? p2[0]!;
  const critical = lead.priority === "P1";

  return (
    <div
      role="alert"
      className={cn(
        "flex flex-wrap items-center justify-between gap-3 border-y px-0 py-2",
        critical
          ? "border-state-critical/50 bg-state-critical/10 px-3"
          : "border-state-warning/40 bg-state-warning/10 px-3",
      )}
    >
      <div className="flex items-start gap-2">
        <Siren
          className={cn(
            "mt-0.5 h-4 w-4 shrink-0",
            critical ? "text-state-critical" : "text-state-warning",
          )}
          aria-hidden
        />
        <div>
          <p className="type-status text-primary">
            {lead.priority} {critical ? "Critical" : "Warning"}
            {p1.length + p2.length > 1
              ? ` · ${p1.length + p2.length} unacknowledged`
              : ""}
          </p>
          <p className="type-body mt-0.5">
            {lead.title} — {lead.process}
          </p>
        </div>
      </div>
      <Button asChild size="sm" variant={critical ? "critical" : "secondary"}>
        <Link href="/alerts">View alerts</Link>
      </Button>
    </div>
  );
}

export function AlertItem({
  alert,
  timeZone,
}: {
  alert: Alert;
  timeZone?: string;
}) {
  return (
    <article className="grid grid-cols-[auto_1fr_auto] items-start gap-2 border-b border-subtle py-2 last:border-0">
      <Badge tone={priorityTone[alert.priority]}>{alert.priority}</Badge>
      <div>
        <p className="type-body">{alert.title}</p>
        <p className="type-meta mt-0.5 text-secondary">
          {alert.process} · {alert.asset} · {alert.source}
        </p>
      </div>
      <time className="type-timestamp" dateTime={alert.observedAt}>
        {formatTimestamp(alert.observedAt, timeZone)}
      </time>
    </article>
  );
}
