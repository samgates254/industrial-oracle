import { Badge } from "@/components/ui/badge";

export function ArchitectureIntent({
  visual,
  not,
  stages,
}: {
  visual: string;
  not: string;
  stages: readonly string[];
}) {
  return (
    <div className="mt-4 border-t border-subtle pt-4">
      <p className="type-panel">Visual contract</p>
      <p className="type-body mt-2">
        Primary visual: <span className="type-ident">{visual}</span>
        <span className="text-muted"> — not a {not}.</span>
      </p>
      <ol className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-5">
        {stages.map((stage) => (
          <li
            key={stage}
            className="flex min-h-[4.5rem] flex-col justify-between border border-subtle p-2"
          >
            <span className="type-kpi-label">{stage}</span>
            <Badge tone="neutral">Not built</Badge>
          </li>
        ))}
      </ol>
    </div>
  );
}
