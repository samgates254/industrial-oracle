import type { FlowKind } from "@/types/topology";
import { cn } from "@/lib/cn";

const items: { flow: FlowKind; label: string; className: string }[] = [
  { flow: "production", label: "Production flow", className: "bg-strong" },
  { flow: "material", label: "Material flow", className: "bg-data-inventory" },
  { flow: "energy", label: "Energy relationship", className: "border-t border-dashed border-data-energy" },
];

export function TopologyLegend() {
  return (
    <ul className="flex flex-wrap gap-4" aria-label="Flow legend">
      {items.map((item) => (
        <li key={item.flow} className="flex items-center gap-2">
          <span className={cn("inline-block h-px w-6", item.className)} aria-hidden />
          <span className="type-meta text-secondary">{item.label}</span>
        </li>
      ))}
      <li className="flex items-center gap-2">
        <span className="inline-block h-px w-6 bg-state-warning" aria-hidden />
        <span className="type-meta text-secondary">Constrained path</span>
      </li>
    </ul>
  );
}
