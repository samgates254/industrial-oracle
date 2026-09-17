import Link from "next/link";
import type { EvidenceKind } from "@/design-system/tokens";
import type { IntelligenceBlock } from "@/types/operational";
import { Button } from "@/components/ui/button";
import { TruthClassLabel, TruthFrame } from "./truth-class";

export function IntelligenceCallout({ block }: { block: IntelligenceBlock }) {
  return (
    <TruthFrame kind={block.kind} as="article" variant="zone">
      <TruthClassLabel kind={block.kind} />
      <p className="type-body mt-2">{block.body}</p>
      {block.kind === "human-decision" ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button asChild size="sm" variant="secondary">
            <Link href="/optimization">Review</Link>
          </Button>
          <Button
            size="sm"
            variant="primary"
            disabled
            title="Backend authorization required"
          >
            Approve
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled
            title="Backend authorization required"
          >
            Dismiss
          </Button>
        </div>
      ) : null}
    </TruthFrame>
  );
}

export function IntelligenceStack({
  blocks,
  kinds,
}: {
  blocks: IntelligenceBlock[];
  kinds?: EvidenceKind[];
}) {
  const visible = kinds
    ? blocks.filter((block) => kinds.includes(block.kind))
    : blocks;
  return (
    <div className="io-grid">
      {visible.map((block) => (
        <IntelligenceCallout key={block.kind} block={block} />
      ))}
    </div>
  );
}
