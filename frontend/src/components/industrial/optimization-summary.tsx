import type { OptimizationSummary } from "@/types/operational";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { EngineStatus } from "@/features/optimization/engine-status";
import { TruthClassLabel, TruthFrame } from "./truth-class";

export function OptimizationSummaryCard({
  summary,
}: {
  summary: OptimizationSummary;
}) {
  return (
    <TruthFrame kind="optimization-result">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <TruthClassLabel kind="optimization-result" />
        <div className="flex flex-wrap items-center gap-1.5">
          <EngineStatus />
          <Badge tone="demo">Demo copy</Badge>
        </div>
      </div>
      <p className="type-meta mt-2 text-muted">
        This Command Center card is synthetic. Open the engine workspace to compile a
        real factory YAML and run HiGHS.
      </p>
      <dl className="io-readout mt-3">
        <dt>Scenario</dt>
        <dd>{summary.scenarioId}</dd>
        <dt>Decision</dt>
        <dd className="font-sans text-copy font-normal">{summary.decisionVariablesNote}</dd>
        <dt>Constraint</dt>
        <dd className="font-sans text-copy font-normal">
          {summary.bindingConstraints[0] ?? "—"}
        </dd>
        <dt>Result</dt>
        <dd className="font-sans text-copy font-normal">{summary.expectedImpact}</dd>
      </dl>
      <details className="mt-3">
        <summary className="cursor-pointer type-meta text-secondary">
          Solver metadata
        </summary>
        <dl className="io-readout mt-2">
          <dt>Model</dt>
          <dd>
            {summary.modelId} {summary.modelVersion}
          </dd>
          <dt>Solver</dt>
          <dd>{summary.solver}</dd>
          <dt>Solve time</dt>
          <dd>{summary.solveTimeMs !== null ? `${summary.solveTimeMs} ms` : "—"}</dd>
          <dt>Gap</dt>
          <dd>
            {summary.optimalityGapPct !== null
              ? `${summary.optimalityGapPct.toFixed(1)}%`
              : "—"}
          </dd>
        </dl>
      </details>
      <div className="mt-3">
        <Button asChild size="sm" variant="optimize">
          <Link href="/optimization">Run real engine</Link>
        </Button>
      </div>
    </TruthFrame>
  );
}
