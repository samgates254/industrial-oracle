import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import { formatSigned } from "@/lib/format";
import { cn } from "@/lib/cn";

export function TrendIndicator({
  value,
  unit,
  precision = 1,
  invert = false,
}: {
  value: number;
  unit?: string;
  precision?: number;
  invert?: boolean;
}) {
  const upIsGood = !invert;
  const positive = value > 0;
  const negative = value < 0;
  const good = value === 0 ? null : upIsGood ? positive : negative;
  const Icon = value > 0 ? TrendingUp : value < 0 ? TrendingDown : Minus;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 type-meta font-mono",
        good === true && "text-state-success",
        good === false && "text-state-critical",
        good === null && "text-muted",
      )}
    >
      <Icon className="h-3 w-3" aria-hidden />
      <span>Δ {formatSigned(value, precision, unit)}</span>
    </span>
  );
}
