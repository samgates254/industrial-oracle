"use client";

import type { PlantTopologySnapshot } from "@/types/topology";
import { TopologyNodeCard } from "./topology-node";
import { TopologyEdgeMark } from "./topology-edge";
import { TopologyLegend } from "./topology-legend";

export function PlantTopology({
  snapshot,
  selectedId,
  onSelect,
}: {
  snapshot: PlantTopologySnapshot;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const ordered = snapshot.sequence.length
    ? snapshot.sequence
        .map((id) => snapshot.nodes.find((node) => node.id === id))
        .filter((node): node is NonNullable<typeof node> => Boolean(node))
        .concat(snapshot.nodes.filter((node) => !snapshot.sequence.includes(node.id)))
    : snapshot.nodes;

  const constraintLabel =
    snapshot.nodes.find((node) => node.constraintId)?.constraintLabel ?? "none";

  return (
    <figure className="io-zone py-3">
      <figcaption className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="type-panel">Process topology</p>
          <p className="type-secondary mt-1">
            Rendered from backend nodes/edges. Binding constraint: {constraintLabel}.
          </p>
        </div>
        <TopologyLegend />
      </figcaption>

      {ordered.length === 0 ? (
        <p className="type-body text-secondary">No topology nodes. Ingest events first.</p>
      ) : (
        <ol className="flex flex-col">
          {ordered.map((node, index) => {
            const next = ordered[index + 1];
            const edge = next
              ? snapshot.edges.find((item) => item.from === node.id && item.to === next.id)
              : undefined;
            return (
              <li key={node.id}>
                <TopologyNodeCard
                  node={node}
                  selected={selectedId === node.id}
                  onSelect={onSelect}
                />
                {edge ? (
                  <div className="flex justify-center">
                    <TopologyEdgeMark
                      flow={edge.flow}
                      label={edge.label}
                      constrained={edge.constrained}
                    />
                  </div>
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
    </figure>
  );
}
