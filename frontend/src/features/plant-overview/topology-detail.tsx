"use client";

import Link from "next/link";
import type { Bottleneck } from "@/types/operational";
import type { TopologyNode } from "@/types/topology";
import { Button } from "@/components/ui/button";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { FreshnessIndicator } from "@/components/industrial/freshness-indicator";
import { TruthClassLabel } from "@/components/industrial/truth-class";
import { formatNumber, moneyOrUnavailable } from "@/lib/format";

export function TopologyDetail({
  node,
  bottleneck,
  onClear,
}: {
  node: TopologyNode | null;
  bottleneck: Bottleneck | null;
  onClear: () => void;
}) {
  if (!node) {
    return (
      <div className="io-zone py-3">
        <p className="type-panel">Inspector</p>
        <p className="type-secondary mt-2">Select a node.</p>
      </div>
    );
  }

  const showRates = node.id === "line_02" && bottleneck;

  return (
    <article aria-labelledby="node-detail-title">
      <div className="flex items-start justify-between gap-2">
        <div>
          <TruthClassLabel kind="system-fact" />
          <h2 id="node-detail-title" className="type-section mt-2">
            {node.name}
          </h2>
          <p className="type-ident text-muted">{node.kindLabel}</p>
        </div>
        <button
          type="button"
          className="type-meta text-secondary hover:text-primary"
          onClick={onClear}
        >
          Clear
        </button>
      </div>
      <div className="mt-2">
        {node.status === "normal" ? (
          <span className="type-status text-muted">Normal</span>
        ) : (
          <StatusIndicator state={node.status} />
        )}
      </div>
      <dl className="io-readout mt-3">
        {node.constraintLabel ? (
          <>
            <dt>Constraint</dt>
            <dd>{node.constraintLabel}</dd>
          </>
        ) : null}
        {showRates && bottleneck ? (
          <>
            <dt>Current</dt>
            <dd>
              {formatNumber(bottleneck.currentRate, 0)} {bottleneck.rateUnit}
            </dd>
            <dt>Target</dt>
            <dd>
              {formatNumber(bottleneck.targetRate, 0)} {bottleneck.rateUnit}
            </dd>
            <dt>Utilization</dt>
            <dd>{formatNumber(bottleneck.utilizationPct, 1)}%</dd>
            <dt>Impact</dt>
            <dd className="font-sans text-copy font-normal text-secondary">
              {moneyOrUnavailable(bottleneck.economicImpactPerHour, "Not computed")}
            </dd>
          </>
        ) : null}
        {node.metrics
          .filter((metric) => !(showRates && (metric.label === "Current" || metric.label === "Target" || metric.label === "Utilization")))
          .map((metric) => (
            <div key={metric.label} className="contents">
              <dt>{metric.label}</dt>
              <dd className="font-sans text-copy font-normal">{metric.value}</dd>
            </div>
          ))}
      </dl>
      <p className="type-body mt-3">{node.statusNote}</p>
      <div className="mt-2">
        <FreshnessIndicator
          state={node.freshness}
          observedAt={node.observedAt}
          nowIso={node.observedAt}
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-2 border-t border-subtle pt-3">
        {node.actions.map((action) =>
          action.enabled ? (
            <Button key={action.label} asChild size="sm">
              <Link href={action.href}>{action.label}</Link>
            </Button>
          ) : (
            <Button
              key={action.label}
              size="sm"
              disabled
              title={action.reason ?? "Unavailable"}
            >
              {action.label}
            </Button>
          ),
        )}
      </div>
    </article>
  );
}
