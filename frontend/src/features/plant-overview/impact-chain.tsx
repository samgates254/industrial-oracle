import type { TopologyImpact } from "@/types/topology";
import { CausalChain } from "@/components/industrial/causal-chain";
import { TruthClassLabel, TruthFrame } from "@/components/industrial/truth-class";

export function ImpactChain({ impacts }: { impacts: TopologyImpact[] }) {
  return (
    <TruthFrame kind="system-fact" aria-labelledby="impact-heading">
      <TruthClassLabel kind="system-fact" />
      <h2 id="impact-heading" className="type-section mt-2">
        Impact
      </h2>
      <div className="mt-3">
        <CausalChain
          steps={impacts.map((item, index) => ({
            id: item.id,
            label: item.label,
            detail: item.detail,
            tone: index === 0 ? "constraint" : "default",
          }))}
        />
      </div>
    </TruthFrame>
  );
}
