import { cn } from "@/lib/cn";

export function Sparkline({
  values,
  className,
  color = "var(--io-data-telemetry)",
  threshold,
}: {
  values: number[];
  className?: string;
  color?: string;
  threshold?: number;
}) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const w = 72;
  const h = 28;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / span) * (h - 2) - 1;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const last = values[values.length - 1]!;
  const lastX = w;
  const lastY = h - ((last - min) / span) * (h - 2) - 1;
  const thresholdY =
    threshold === undefined ? null : h - ((threshold - min) / span) * (h - 2) - 1;

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      className={cn("h-7 w-[72px] overflow-visible", className)}
      aria-hidden
    >
      {thresholdY !== null ? (
        <line
          x1="0"
          x2={w}
          y1={thresholdY}
          y2={thresholdY}
          stroke="var(--io-text-muted)"
          strokeDasharray="2 3"
          strokeWidth="0.75"
        />
      ) : null}
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.25"
        points={pts}
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={lastX} cy={lastY} r="1.6" fill={color} />
    </svg>
  );
}

export function TimeSeriesChart({
  values,
  labels,
  color = "var(--io-data-telemetry)",
  threshold,
  thresholdLabel,
}: {
  values: number[];
  labels?: string[];
  color?: string;
  threshold?: number;
  thresholdLabel?: string;
}) {
  if (values.length < 2) return null;
  const min = Math.min(...values, threshold ?? Infinity);
  const max = Math.max(...values, threshold ?? -Infinity);
  const pad = (max - min) * 0.12 || 1;
  const lo = min - pad;
  const hi = max + pad;
  const span = hi - lo;
  const w = 320;
  const h = 96;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - lo) / span) * h;
    return { x, y, v };
  });
  const d = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const thresholdY =
    threshold === undefined ? null : h - ((threshold - lo) / span) * h;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-24 w-full" role="img" aria-label="Time series">
      {thresholdY !== null ? (
        <>
          <line
            x1="0"
            x2={w}
            y1={thresholdY}
            y2={thresholdY}
            stroke="var(--io-text-muted)"
            strokeDasharray="3 4"
            strokeWidth="1"
          />
          {thresholdLabel ? (
            <text
              x={w - 4}
              y={(thresholdY ?? 0) - 4}
              textAnchor="end"
              fill="var(--io-text-muted)"
              fontSize="9"
            >
              {thresholdLabel} {threshold}
            </text>
          ) : null}
        </>
      ) : null}
      <path d={d} fill="none" stroke={color} strokeWidth="1.5" />
      {pts[pts.length - 1] ? (
        <circle
          cx={pts[pts.length - 1]!.x}
          cy={pts[pts.length - 1]!.y}
          r="2.2"
          fill={color}
        />
      ) : null}
      {labels?.[0] ? (
        <text x="0" y={h - 2} fill="var(--io-text-muted)" fontSize="9">
          {labels[0]}
        </text>
      ) : null}
    </svg>
  );
}
