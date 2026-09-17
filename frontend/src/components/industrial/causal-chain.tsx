import { cn } from "@/lib/cn";

export type CausalStep = {
  id: string;
  label: string;
  detail: string;
  tone?: "constraint" | "default";
};

export function CausalChain({ steps }: { steps: CausalStep[] }) {
  return (
    <ol className="flex flex-col">
      {steps.map((step, index) => (
        <li key={step.id} className="grid grid-cols-[0.75rem_1fr] gap-2">
          <div className="flex flex-col items-center">
            <span
              className={cn(
                "mt-1.5 h-1.5 w-1.5 shrink-0",
                step.tone === "constraint" ? "bg-state-warning" : "bg-strong",
              )}
              aria-hidden
            />
            {index < steps.length - 1 ? (
              <span className="mt-1 w-px flex-1 bg-strong" aria-hidden />
            ) : null}
          </div>
          <div className={cn("pb-3", index === steps.length - 1 && "pb-0")}>
            <p className="type-ident">{step.label}</p>
            <p className="type-meta text-secondary">{step.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
