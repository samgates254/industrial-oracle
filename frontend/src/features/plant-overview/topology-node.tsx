"use client";

import { Bolt, Factory, Gauge, Network, Package, Truck } from "lucide-react";
import type { TopologyNode, TopologyNodeKind } from "@/types/topology";
import { cn } from "@/lib/cn";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { ConstraintMarker } from "@/components/industrial/constraint-marker";

const kindIcon: Record<TopologyNodeKind, typeof Factory> = {
  area: Factory,
  line: Gauge,
  machine: Network,
  buffer: Package,
  logistics: Truck,
  energy: Bolt,
};

export function TopologyNodeCard({
  node,
  selected,
  onSelect,
}: {
  node: TopologyNode;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const Icon = kindIcon[node.kind];
  const isBottleneck = node.id === "line_02" || node.id === "m_204";

  return (
    <button
      type="button"
      id={`topo-node-${node.id}`}
      aria-pressed={selected}
      onClick={() => onSelect(node.id)}
      className={cn(
        "w-full border bg-command px-3 py-2 text-left transition-colors duration-fast ease-io",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus",
        selected ? "border-focus" : "border-default hover:border-strong",
        isBottleneck && !selected && "border-state-warning/70",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <Icon className="h-3.5 w-3.5 shrink-0 text-muted" aria-hidden strokeWidth={1.75} />
          <div className="min-w-0">
            <p className="type-ident leading-tight">{node.name}</p>
            <p className="type-kpi-label">{node.kindLabel}</p>
          </div>
        </div>
        {node.status === "normal" ? (
          <span className="type-status text-muted">Normal</span>
        ) : (
          <StatusIndicator state={node.status} />
        )}
      </div>
      {isBottleneck && node.constraintLabel ? (
        <div className="mt-1.5">
          <ConstraintMarker label={node.constraintLabel} />
        </div>
      ) : null}
    </button>
  );
}
