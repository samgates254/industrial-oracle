import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-control px-1.5 py-0.5 type-status",
  {
    variants: {
      tone: {
        neutral: "bg-elevated text-secondary border border-default",
        normal: "bg-state-normal/15 text-state-normal border border-state-normal/40",
        warning: "bg-state-warning/15 text-state-warning border border-state-warning/40",
        critical: "bg-state-critical/15 text-state-critical border border-state-critical/40",
        degraded: "bg-state-degraded/15 text-state-degraded border border-state-degraded/40",
        offline: "bg-elevated text-state-offline border border-default",
        maintenance: "bg-state-maintenance/15 text-state-maintenance border border-state-maintenance/40",
        brand: "bg-brand-muted text-brand border border-brand/40",
        ai: "bg-ai-recommendation/15 text-ai-recommendation border border-dashed border-ai-recommendation/50",
        demo: "bg-state-warning/10 text-state-warning border border-state-warning/40",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export function Badge({
  className,
  tone,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}
