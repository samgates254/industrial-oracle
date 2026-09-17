import type { SystemState } from "@/design-system/tokens";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { cn } from "@/lib/cn";

export function StatusRail({
  items,
  className,
}: {
  items: { label: string; value: string; state?: SystemState }[];
  className?: string;
}) {
  return (
    <ul className={cn("io-rail", className)} aria-label="Operational status">
      {items.map((item) => (
        <li key={item.label} className="flex items-baseline gap-2">
          <span className="type-kpi-label">{item.label}</span>
          {item.state ? (
            <StatusIndicator state={item.state} label={item.value} />
          ) : (
            <span className="type-ident text-primary">{item.value}</span>
          )}
        </li>
      ))}
    </ul>
  );
}
