import type { TopologyCounts } from "@/types/topology";
import { StatusRail } from "@/components/industrial/status-rail";

export function PlantStatusStrip({ counts }: { counts: TopologyCounts }) {
  return (
    <StatusRail
      items={[
        { label: "Areas", value: String(counts.areas) },
        { label: "Lines", value: String(counts.lines) },
        { label: "Machines", value: String(counts.machines) },
        { label: "Constraints", value: String(counts.constraints) },
      ]}
    />
  );
}
