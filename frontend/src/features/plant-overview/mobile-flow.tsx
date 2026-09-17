"use client";

import type { PlantTopologySnapshot, TopologyNode } from "@/types/topology";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { ConstraintMarker } from "@/components/industrial/constraint-marker";
import { cn } from "@/lib/cn";

export function MobileFlow({
  snapshot,
  selectedId,
  onSelect,
}: {
  snapshot: PlantTopologySnapshot;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const ordered = snapshot.sequence
    .map((id) => snapshot.nodes.find((node) => node.id === id))
    .filter((node): node is TopologyNode => Boolean(node));
  const constraint = snapshot.nodes.find((node) => node.id === "m_204");

  return (
    <div className="flex flex-col gap-3 md:hidden">
      <section className="rounded-panel border border-state-warning/50 bg-panel p-panel-pad">
        <p className="type-panel">Active constraint</p>
        <h2 className="type-section mt-1">{snapshot.bottleneck?.location}</h2>
        {constraint ? (
          <button
            type="button"
            className="mt-2 w-full text-left"
            onClick={() => onSelect(constraint.id)}
          >
            <ConstraintMarker label={constraint.name} />
            <p className="type-body mt-2">{snapshot.bottleneck?.kind}</p>
            <p className="type-telemetry mt-1">
              {snapshot.bottleneck?.currentRate} → {snapshot.bottleneck?.targetRate}{" "}
              {snapshot.bottleneck?.rateUnit}
            </p>
          </button>
        ) : null}
      </section>

      <section>
        <p className="type-panel mb-2">Critical flow</p>
        <ol className="flex flex-col">
          {ordered.map((node, index) => (
            <li key={node.id}>
              {index > 0 ? (
                <p className="py-1 text-center type-kpi-label text-muted">↓</p>
              ) : null}
              <button
                type="button"
                aria-pressed={selectedId === node.id}
                onClick={() => onSelect(node.id)}
                className={cn(
                  "flex w-full items-center justify-between gap-2 rounded-panel border p-panel-pad text-left",
                  selectedId === node.id ? "border-focus" : "border-default",
                  (node.id === "line_02" || node.id === "m_204") &&
                    "border-state-warning/70",
                )}
              >
                <span>
                  <span className="type-kpi-label block">{node.kindLabel}</span>
                  <span className="type-section">{node.name}</span>
                </span>
                <StatusIndicator state={node.status} />
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
