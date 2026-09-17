import type { Kpi } from "@/types/operational";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/cn";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { FreshnessIndicator } from "./freshness-indicator";
import { Sparkline } from "./sparkline";
import { TrendIndicator } from "./trend-indicator";

const domainColor: Record<string, string> = {
  production: "var(--io-data-production)",
  energy: "var(--io-data-energy)",
  inventory: "var(--io-data-inventory)",
  logistics: "var(--io-data-logistics)",
  telemetry: "var(--io-data-telemetry)",
};

export function KpiCard({ kpi, nowIso }: { kpi: Kpi; nowIso: string }) {
  return (
    <article
      className={cn(
        "flex min-h-[148px] flex-col justify-between overflow-hidden rounded-panel border border-default bg-panel p-panel-pad",
        kpi.hierarchy === "primary" && "border-strong",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="type-kpi-label leading-tight">{kpi.label}</p>
          <p className="type-kpi mt-1 whitespace-nowrap">
            {formatNumber(kpi.value, kpi.precision)}
            <span className="ml-1 font-sans text-meta font-normal text-muted">
              {kpi.unit}
            </span>
          </p>
        </div>
        {kpi.sparkline ? (
          <Sparkline
            className="hidden shrink-0 sm:block"
            values={kpi.sparkline}
            color={domainColor[kpi.domain] ?? "var(--io-data-telemetry)"}
            threshold={kpi.target ?? undefined}
          />
        ) : null}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
        {kpi.target !== null ? (
          <p className="type-meta text-secondary">
            Target {formatNumber(kpi.target, kpi.precision)} {kpi.unit}
          </p>
        ) : null}
        <TrendIndicator
          value={kpi.delta}
          unit={kpi.deltaUnit}
          precision={kpi.precision}
        />
        <StatusIndicator state={kpi.status} />
      </div>

      {kpi.diagnostics?.length ? (
        <p className="mt-2 type-meta text-secondary">
          {kpi.diagnostics.map((d) => `${d.label} ${d.value}`).join(" · ")}
        </p>
      ) : null}

      <div className="mt-2 flex items-center justify-between gap-2">
        <span className="type-meta text-muted">{kpi.timeContext}</span>
        <FreshnessIndicator
          state="updated"
          observedAt={kpi.observedAt}
          nowIso={nowIso}
        />
      </div>
    </article>
  );
}
