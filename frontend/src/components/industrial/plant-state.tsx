import type { CommandCenterSnapshot, Kpi } from "@/types/operational";
import { formatNumber } from "@/lib/format";
import { cn } from "@/lib/cn";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { FreshnessIndicator } from "./freshness-indicator";
import { TrendIndicator } from "./trend-indicator";
import { TruthClassLabel } from "./truth-class";

function MetricCell({
  kpi,
  className,
}: {
  kpi: Kpi;
  className?: string;
}) {
  return (
    <div className={cn("min-w-0 p-panel-pad", className)}>
      <p className="type-kpi-label truncate">{kpi.label}</p>
      <p className="mt-1 flex items-baseline gap-1.5 whitespace-nowrap">
        <span className="type-kpi-sm">
          {formatNumber(kpi.value, kpi.precision)}
        </span>
        <span className="type-meta text-muted">{kpi.unit}</span>
      </p>
      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
        <TrendIndicator
          value={kpi.delta}
          unit={kpi.deltaUnit}
          precision={kpi.precision}
        />
        <StatusIndicator state={kpi.status} />
      </div>
      {kpi.target !== null ? (
        <p className="type-meta mt-1 text-muted">
          Target {formatNumber(kpi.target, kpi.precision)} {kpi.unit}
        </p>
      ) : null}
    </div>
  );
}

export function PlantStateStrip({ snapshot }: { snapshot: CommandCenterSnapshot }) {
  const { meta, health, kpis } = snapshot;

  return (
    <section aria-labelledby="plant-state-heading" className="truth-fact rounded-panel border border-default bg-panel">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-subtle p-panel-pad">
        <div className="min-w-0">
          <TruthClassLabel kind="system-fact" />
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <h2 id="plant-state-heading" className="type-section">
              Plant state
            </h2>
            <StatusIndicator state={health.status} label={`Plant ${health.status}`} />
          </div>
          <p className="type-body mt-1 max-w-3xl">{health.summary}</p>
          <p className="type-meta mt-1 text-muted">
            {meta.plant.name} · {meta.shift.name}
          </p>
        </div>
        <FreshnessIndicator
          state="updated"
          observedAt={meta.snapshotAt}
          nowIso={meta.snapshotAt}
          timeZone={meta.plant.timezone}
        />
      </div>
      <div
        className="grid grid-cols-2 divide-x divide-subtle sm:grid-cols-3 xl:grid-cols-5"
        aria-label="Plant metrics"
      >
        {kpis.map((kpi, index) => (
          <MetricCell
            key={kpi.id}
            kpi={kpi}
            className={cn(
              index === 2 && "hidden sm:block",
              index >= 3 && "hidden xl:block",
            )}
          />
        ))}
      </div>
      {kpis[0]?.diagnostics?.length ? (
        <p className="border-t border-subtle px-panel-pad py-2 type-meta text-secondary">
          OEE {kpis[0].diagnostics.map((d) => `${d.label} ${d.value}`).join(" · ")}
        </p>
      ) : null}
    </section>
  );
}
