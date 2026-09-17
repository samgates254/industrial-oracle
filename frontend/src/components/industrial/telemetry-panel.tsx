import type { TelemetrySeries } from "@/types/operational";
import { formatNumber } from "@/lib/format";
import { Panel, SectionHeader } from "@/components/ui/panel";
import { FreshnessIndicator } from "./freshness-indicator";
import { TimeSeriesChart } from "./sparkline";

const domainStroke: Record<string, string> = {
  production: "var(--io-data-production)",
  energy: "var(--io-data-energy)",
  logistics: "var(--io-data-logistics)",
  telemetry: "var(--io-data-telemetry)",
};

export function TelemetryPanel({
  series,
  nowIso,
}: {
  series: TelemetrySeries;
  nowIso: string;
}) {
  return (
    <Panel>
      <SectionHeader
        eyebrow={series.domain}
        title={series.label}
        actions={
          <FreshnessIndicator
            state={series.freshness}
            observedAt={series.observedAt}
            nowIso={nowIso}
          />
        }
      />
      <p className="font-mono text-kpi-sm tabular text-primary">
        {formatNumber(series.current, series.unit === "MW" ? 2 : 0)}
        <span className="ml-1 font-sans text-meta font-normal text-muted">
          {series.unit}
        </span>
      </p>
      <div className="mt-2">
        <TimeSeriesChart
          values={series.points.map((p) => p.v)}
          color={domainStroke[series.domain] ?? "var(--io-data-telemetry)"}
          threshold={series.threshold?.value}
          thresholdLabel={series.threshold?.label}
        />
      </div>
    </Panel>
  );
}
