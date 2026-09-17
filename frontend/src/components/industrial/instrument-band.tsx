import type { Kpi } from "@/types/operational";
import { formatNumber, formatSigned } from "@/lib/format";
import { StatusIndicator } from "@/components/ui/status-indicator";

export function InstrumentBand({ kpis }: { kpis: Kpi[] }) {
  return (
    <section aria-label="Plant instruments" className="overflow-x-auto">
      <table className="w-full min-w-[40rem] max-w-5xl text-table">
        <caption className="sr-only">Operational readings versus target</caption>
        <thead>
          <tr className="border-b border-subtle text-left">
            <th className="py-1.5 type-kpi-label font-medium">Reading</th>
            <th className="py-1.5 type-kpi-label font-medium">Value</th>
            <th className="py-1.5 type-kpi-label font-medium">Target</th>
            <th className="py-1.5 type-kpi-label font-medium">Δ</th>
            <th className="py-1.5 type-kpi-label font-medium">State</th>
            <th className="hidden py-1.5 type-kpi-label font-medium lg:table-cell">Context</th>
          </tr>
        </thead>
        <tbody>
          {kpis.map((kpi) => (
            <tr key={kpi.id} className="border-b border-subtle last:border-0">
              <td className="py-1.5 type-body">{kpi.label}</td>
              <td className="py-1.5 type-telemetry whitespace-nowrap">
                {formatNumber(kpi.value, kpi.precision)} {kpi.unit}
              </td>
              <td className="py-1.5 type-telemetry whitespace-nowrap text-secondary">
                {kpi.target !== null
                  ? `${formatNumber(kpi.target, kpi.precision)} ${kpi.unit}`
                  : "—"}
              </td>
              <td className="py-1.5 type-telemetry whitespace-nowrap">
                {formatSigned(kpi.delta, kpi.precision, kpi.deltaUnit)}
              </td>
              <td className="py-1.5">
                {kpi.status === "normal" ? (
                  <span className="type-status text-muted">Normal</span>
                ) : (
                  <StatusIndicator state={kpi.status} />
                )}
              </td>
              <td className="hidden py-1.5 type-meta lg:table-cell">{kpi.timeContext}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {kpis[0]?.diagnostics?.length ? (
        <p className="mt-2 type-meta text-secondary">
          OEE {kpis[0].diagnostics.map((d) => `${d.label} ${d.value}`).join(" · ")}
        </p>
      ) : null}
    </section>
  );
}
