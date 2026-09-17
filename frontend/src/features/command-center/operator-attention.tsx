import Link from "next/link";
import type { AttentionItem } from "@/types/operational";
import { Button } from "@/components/ui/button";
import { TruthClassLabel, TruthFrame } from "@/components/industrial/truth-class";

export function OperatorAttention({ items }: { items: AttentionItem[] }) {
  return (
    <TruthFrame kind="human-decision" aria-labelledby="decision-title">
      <TruthClassLabel kind="human-decision" />
      <h2 id="decision-title" className="type-section mt-2">
        Authorization required
      </h2>
      <p className="type-meta mt-1 text-secondary">
        The system has analyzed this. A human must decide. AI cannot dispatch the plant.
      </p>
      <ol className="mt-3 flex flex-col">
        {items.map((item, index) => (
          <li
            key={item.id}
            className="grid grid-cols-[2rem_1fr] gap-2 border-b border-subtle py-2 last:border-0"
          >
            <span className="type-ident text-muted">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div>
              <Link href={item.href} className="type-body text-primary hover:text-brand">
                {item.title}
              </Link>
              <p className="type-meta text-secondary">{item.detail}</p>
            </div>
          </li>
        ))}
      </ol>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button asChild size="sm" variant="primary">
          <Link href="/optimization">Review decision</Link>
        </Button>
        <Button size="sm" disabled title="Backend authorization required">
          Approve
        </Button>
        <Button size="sm" variant="ghost" disabled title="Backend authorization required">
          Dismiss
        </Button>
      </div>
    </TruthFrame>
  );
}
