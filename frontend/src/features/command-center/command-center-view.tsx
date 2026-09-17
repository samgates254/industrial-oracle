import type { CommandCenterSnapshot } from "@/types/operational";
import { AlertBanner } from "@/components/industrial/alerts";
import { BottleneckCard } from "@/components/industrial/bottleneck";
import { EventTimeline } from "@/components/industrial/event-timeline";
import { InstrumentBand } from "@/components/industrial/instrument-band";
import { IntelligenceStack } from "@/components/industrial/intelligence";
import { OptimizationSummaryCard } from "@/components/industrial/optimization-summary";
import { StatusRail } from "@/components/industrial/status-rail";
import { TelemetryRail } from "@/components/industrial/telemetry-rail";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { formatTimestamp } from "@/lib/format";
import { OperatorAttention } from "./operator-attention";
import type { CausalStep } from "@/components/industrial/causal-chain";

function constraintChain(snapshot: CommandCenterSnapshot): CausalStep[] {
  const bn = snapshot.bottleneck;
  if (!bn) return [];
  return [
    {
      id: "asset",
      label: bn.constraintAsset,
      detail: bn.why,
      tone: "constraint",
    },
    {
      id: "location",
      label: bn.location,
      detail: `${bn.currentRate} ${bn.rateUnit} versus target ${bn.targetRate}`,
    },
  ];
}

export function CommandCenterView({ snapshot }: { snapshot: CommandCenterSnapshot }) {
  const { meta, health, kpis, bottleneck, optimization, alerts, telemetry, attention, intelligence } =
    snapshot;

  return (
    <div className="io-page flex flex-col gap-5">
      {meta.source === "demo" ? (
        <p className="type-meta text-muted" role="status">
          {meta.disclaimer}
        </p>
      ) : null}

      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <Breadcrumbs
            items={[
              { href: "/command", label: "Command" },
              { label: "Overview" },
            ]}
          />
          <h1 className="type-page-title mt-1">Command Center</h1>
        </div>
      </header>

      <StatusRail
        items={[
          { label: "Plant", value: health.status, state: health.status },
          { label: "Shift", value: meta.shift.name },
          {
            label: "Link",
            value: meta.connectivity === "live" ? "Connected" : meta.connectivity,
            state: meta.connectivity === "live" ? "success" : "offline",
          },
          { label: "Snapshot", value: formatTimestamp(meta.snapshotAt, meta.plant.timezone) },
        ]}
      />

      <p className="type-body text-secondary">{health.summary}</p>

      <div className="order-2 md:order-none">
        <InstrumentBand kpis={kpis} />
      </div>

      <div className="order-1 md:order-none">
        <AlertBanner alerts={alerts} />
      </div>

      <section
        aria-label="Constraint and decision"
        className="order-3 grid grid-cols-1 gap-8 xl:grid-cols-[minmax(0,1.35fr)_minmax(18rem,0.85fr)] md:order-none"
      >
        {bottleneck ? (
          <BottleneckCard bottleneck={bottleneck} chain={constraintChain(snapshot)} />
        ) : null}
        <OperatorAttention items={attention} />
      </section>

      <div className="order-4 md:order-none">
        <OptimizationSummaryCard summary={optimization} />
      </div>

      <div className="order-5 md:order-none">
        <IntelligenceStack blocks={intelligence} kinds={["ai-interpretation"]} />
      </div>

      <div className="order-6 grid grid-cols-1 gap-8 lg:grid-cols-2 md:order-none">
        <EventTimeline alerts={alerts} timeZone={meta.plant.timezone} />
        <TelemetryRail series={telemetry} nowIso={meta.snapshotAt} />
      </div>
    </div>
  );
}
