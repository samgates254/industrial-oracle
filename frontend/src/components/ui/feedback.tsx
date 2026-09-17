import { AlertCircle, Inbox, Loader2 } from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "./button";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("animate-pulse rounded-control bg-elevated", className)}
      aria-hidden
    />
  );
}

export function LoadingState({
  label = "Loading operational data",
}: {
  label?: string;
}) {
  return (
    <div
      className="flex items-center gap-2 text-secondary"
      role="status"
      aria-live="polite"
    >
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
      <span className="type-body">{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  reason,
  actionLabel,
  onAction,
}: {
  title: string;
  reason: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex flex-col items-start gap-3 py-6">
      <Inbox className="h-5 w-5 text-muted" aria-hidden />
      <div>
        <h2 className="type-section">{title}</h2>
        <p className="type-secondary mt-1 max-w-prose">{reason}</p>
      </div>
      {actionLabel ? (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}

export function ErrorState({
  title,
  when,
  correlationId,
  remaining,
  actionLabel,
  onAction,
}: {
  title: string;
  when?: string;
  correlationId?: string;
  remaining?: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div
      className="flex flex-col items-start gap-3 rounded-panel border border-state-critical/40 bg-state-critical/10 p-panel-pad"
      role="alert"
    >
      <div className="flex items-center gap-2 text-state-critical">
        <AlertCircle className="h-4 w-4" aria-hidden />
        <h2 className="type-section text-state-critical">{title}</h2>
      </div>
      <dl className="grid gap-1 type-meta text-secondary">
        {when ? (
          <div>
            <dt className="inline text-muted">When: </dt>
            <dd className="inline type-timestamp">{when}</dd>
          </div>
        ) : null}
        {correlationId ? (
          <div>
            <dt className="inline text-muted">Correlation: </dt>
            <dd className="inline type-ident">{correlationId}</dd>
          </div>
        ) : null}
        {remaining ? (
          <div>
            <dt className="inline text-muted">Still available: </dt>
            <dd className="inline">{remaining}</dd>
          </div>
        ) : null}
      </dl>
      {actionLabel ? (
        <Button variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
