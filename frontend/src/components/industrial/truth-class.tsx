import { CircleDot, FunctionSquare, MessageSquareDashed, UserCheck } from "lucide-react";
import type { EvidenceKind } from "@/design-system/tokens";
import { truthClassMeta } from "@/design-system/visual-architecture";
import { cn } from "@/lib/cn";

const icons: Record<EvidenceKind, typeof CircleDot> = {
  "system-fact": CircleDot,
  "optimization-result": FunctionSquare,
  "ai-interpretation": MessageSquareDashed,
  "human-decision": UserCheck,
};

export function TruthClassLabel({
  kind,
  className,
}: {
  kind: EvidenceKind;
  className?: string;
}) {
  const meta = truthClassMeta[kind];
  const Icon = icons[kind];
  return (
    <p className={cn("type-panel flex flex-wrap items-center gap-1.5", className)}>
      <Icon aria-hidden className="h-3.5 w-3.5 shrink-0" strokeWidth={1.75} />
      <span>{meta.label}</span>
      <span className="font-normal normal-case tracking-normal text-muted">{meta.note}</span>
    </p>
  );
}

export function TruthFrame({
  kind,
  children,
  className,
  variant = "zone",
  as: Comp = "section",
  ...props
}: {
  kind: EvidenceKind;
  children: React.ReactNode;
  className?: string;
  variant?: "zone" | "frame";
  as?: "section" | "article" | "div";
} & React.HTMLAttributes<HTMLElement>) {
  const meta = truthClassMeta[kind];
  return (
    <Comp
      className={cn(
        meta.surfaceClass,
        variant === "zone"
          ? "io-zone py-3 pl-3"
          : "rounded-panel border border-default bg-panel p-panel-pad",
        className,
      )}
      data-truth={kind}
      {...props}
    >
      {children}
    </Comp>
  );
}
