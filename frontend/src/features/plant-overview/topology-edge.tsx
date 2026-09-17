import type { FlowKind } from "@/types/topology";
import { cn } from "@/lib/cn";

export function TopologyEdgeMark({
  flow,
  label,
  constrained,
  orientation = "vertical",
}: {
  flow: FlowKind;
  label: string;
  constrained: boolean;
  orientation?: "vertical" | "horizontal";
}) {
  const vertical = orientation === "vertical";
  return (
    <div
      className={cn(
        "flex items-center gap-2",
        vertical ? "flex-col py-1" : "flex-row px-1",
      )}
      role="img"
      aria-label={`${constrained ? "Constrained " : ""}${flow} flow: ${label}`}
    >
      <span
        className={cn(
          vertical ? "h-5 w-px" : "h-px w-5",
          constrained
            ? "bg-state-warning"
            : flow === "energy"
              ? "border-data-energy"
              : "bg-strong",
          flow === "energy" && !constrained && (vertical ? "w-0 border-l border-dashed" : "h-0 border-t border-dashed"),
        )}
      />
      <span
        className={cn(
          "type-kpi-label",
          constrained ? "text-state-warning" : "text-muted",
        )}
      >
        {label}
        {constrained ? " · constrained" : ""}
      </span>
      <span
        aria-hidden
        className={cn(
          "text-meta",
          constrained ? "text-state-warning" : "text-muted",
        )}
      >
        {vertical ? "↓" : "→"}
      </span>
    </div>
  );
}
