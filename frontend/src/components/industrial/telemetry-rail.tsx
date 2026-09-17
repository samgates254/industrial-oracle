import type { TelemetrySeries } from "@/types/operational";
import { formatNumber } from "@/lib/format";
import { FreshnessIndicator } from "./freshness-indicator";
import { Sparkline } from "./sparkline";

const domainStroke: Record<string, string> = {
  production: "var(--io-data-production)",
  energy: "var(--io-data-energy)",
  logistics: "var(--io-data-logistics)",
  telemetry: "var(--io-data-telemetry)",
};

export function TelemetryRail({
  series,
  nowIso,
}: {
  series: TelemetrySeries[];
  nowIso: string;
}) {
  return (
    <section aria-labelledby="telemetry-heading" className="io-hide-mobile md:!block">
      <h2 id="telemetry-heading" className="type-panel mb-2">
        Supporting telemetry
      </h2>
      <table className="w-full text-table">
        <caption className="sr-only">Telemetry versus threshold</caption>
        <thead>
          <tr className="border-b border-subtle text-left">
            <th className="py-1.5 type-kpi-label font-medium">Series</th>
            <th className="py-1.5 type-kpi-label font-medium">Current</th>
            <th className="hidden py-1.5 type-kpi-label font-medium sm:table-cell">
              Threshold
            </th>
            <th className="hidden py-1.5 type-kpi-label font-medium md:table-cell">
              Trend
            </th>
            <th className="py-1.5 type-kpi-label font-medium">Freshness</th>
          </tr>
        </thead>
        <tbody>
          {series.map((item) => (
            <tr key={item.id} className="border-b border-subtle last:border-0">
              <td className="py-1.5 type-body">{item.label}</td>
              <td className="py-1.5 type-telemetry whitespace-nowrap">
                {formatNumber(item.current, item.unit === "MW" ? 2 : 0)} {item.unit}
              </td>
              <td className="hidden py-1.5 type-meta sm:table-cell">
                {item.threshold
                  ? `${item.threshold.label} ${item.threshold.value}`
                  : "—"}
              </td>
              <td className="hidden py-1.5 md:table-cell">
                <Sparkline
                  values={item.points.map((p) => p.v)}
                  color={domainStroke[item.domain] ?? "var(--io-data-telemetry)"}
                  threshold={item.threshold?.value}
                />
              </td>
              <td className="py-1.5">
                <FreshnessIndicator
                  state={item.freshness}
                  observedAt={item.observedAt}
                  nowIso={nowIso}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
