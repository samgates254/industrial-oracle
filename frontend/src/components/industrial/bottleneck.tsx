import Link from "next/link";
import type { Bottleneck } from "@/types/operational";
import { formatNumber, moneyOrUnavailable } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { TruthClassLabel, TruthFrame } from "./truth-class";
import { ConstraintMarker } from "./constraint-marker";
import { CausalChain, type CausalStep } from "./causal-chain";

export function BottleneckCard({
  bottleneck,
  chain,
}: {
  bottleneck: Bottleneck;
  chain?: CausalStep[];
}) {
  const deviation = bottleneck.currentRate - bottleneck.targetRate;

  return (
    <TruthFrame kind="system-fact" aria-labelledby="constraint-title">
      <TruthClassLabel kind="system-fact" />
      <p className="type-panel mt-2">Constraint</p>
      <h2 id="constraint-title" className="type-section mt-1">
        {bottleneck.location} / {bottleneck.constraintAsset}
      </h2>
      <div className="mt-2">
        <ConstraintMarker label={bottleneck.kind} />
      </div>

      <dl className="io-readout mt-3">
        <dt>Capacity</dt>
        <dd>
          {formatNumber(bottleneck.currentRate, 0)} {bottleneck.rateUnit}
        </dd>
        <dt>Target</dt>
        <dd>
          {formatNumber(bottleneck.targetRate, 0)} {bottleneck.rateUnit}
        </dd>
        <dt>Deviation</dt>
        <dd>
          {formatNumber(deviation, 0)} {bottleneck.rateUnit}
        </dd>
        <dt>Utilization</dt>
        <dd>{formatNumber(bottleneck.utilizationPct, 1)}%</dd>
        <dt>Impact</dt>
        <dd className="font-sans text-copy font-normal text-secondary">
          {moneyOrUnavailable(
            bottleneck.economicImpactPerHour,
            "Not computed",
          )}
        </dd>
      </dl>
      <p className="type-meta mt-2 text-muted">{bottleneck.capacityNote}</p>
      <p className="type-body mt-3">{bottleneck.why}</p>

      {chain?.length ? (
        <div className="mt-4">
          <p className="type-panel mb-2">Causal path</p>
          <CausalChain steps={chain} />
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        <Button asChild size="sm">
          <Link href="/analytics">Analyze constraint</Link>
        </Button>
        <Button asChild size="sm">
          <Link href="/plant">Locate on plant</Link>
        </Button>
        <Button asChild size="sm" variant="optimize">
          <Link href="/optimization">View decision</Link>
        </Button>
      </div>
    </TruthFrame>
  );
}
