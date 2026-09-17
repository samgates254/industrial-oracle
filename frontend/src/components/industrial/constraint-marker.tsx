import { AlertTriangle } from "lucide-react";

export function ConstraintMarker({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 border border-state-warning/50 bg-state-warning/10 px-1.5 py-0.5 type-status text-state-warning">
      <AlertTriangle className="h-3 w-3" aria-hidden strokeWidth={1.75} />
      <span>{label}</span>
    </span>
  );
}
