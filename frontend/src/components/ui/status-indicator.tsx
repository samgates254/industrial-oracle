import {
  AlertTriangle,
  CheckCircle2,
  CircleOff,
  Siren,
  Wrench,
  MinusCircle,
} from "lucide-react";
import type { SystemState } from "@/design-system/tokens";
import { cn } from "@/lib/cn";

const config: Record<
  SystemState,
  { label: string; icon: typeof CheckCircle2; className: string }
> = {
  normal: { label: "Normal", icon: CheckCircle2, className: "text-state-normal" },
  success: { label: "Success", icon: CheckCircle2, className: "text-state-success" },
  warning: { label: "Warning", icon: AlertTriangle, className: "text-state-warning" },
  critical: { label: "Critical", icon: Siren, className: "text-state-critical" },
  offline: { label: "Offline", icon: CircleOff, className: "text-state-offline" },
  degraded: { label: "Degraded", icon: MinusCircle, className: "text-state-degraded" },
  maintenance: { label: "Maintenance", icon: Wrench, className: "text-state-maintenance" },
};

export function StatusIndicator({
  state,
  label,
  className,
}: {
  state: SystemState;
  label?: string;
  className?: string;
}) {
  const item = config[state];
  const Icon = item.icon;
  return (
    <span
      className={cn("inline-flex items-center gap-1.5 type-status", item.className, className)}
      role="status"
    >
      <Icon aria-hidden className="h-3.5 w-3.5 shrink-0" strokeWidth={1.75} />
      <span>{label ?? item.label}</span>
    </span>
  );
}
