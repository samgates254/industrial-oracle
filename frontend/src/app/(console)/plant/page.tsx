import type { Metadata } from "next";
import Link from "next/link";
import { getPlantTopology } from "@/lib/api";
import { PlantOverviewView } from "@/features/plant-overview/plant-overview-view";
import { ErrorState } from "@/components/ui/feedback";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Plant Overview",
};

export default async function PlantPage() {
  try {
    const snapshot = await getPlantTopology();
    if (snapshot.nodes.length === 0) {
      return (
        <div className="io-page">
          <ErrorState
            title="Empty topology"
            remaining="No process nodes are available for this plant. Command Center remains available."
          />
          <div className="mt-3">
            <Button asChild size="sm" variant="primary">
              <Link href="/command">Open Command Center</Link>
            </Button>
          </div>
        </div>
      );
    }
    return <PlantOverviewView snapshot={snapshot} />;
  } catch {
    return (
      <div className="io-page">
        <ErrorState
          title="Topology data unavailable"
          remaining="Operational topology could not be loaded. Command Center remains available."
        />
        <div className="mt-3 flex flex-wrap gap-2">
          <Button asChild size="sm">
            <Link href="/plant">Retry</Link>
          </Button>
          <Button asChild size="sm" variant="primary">
            <Link href="/command">Open Command Center</Link>
          </Button>
        </div>
      </div>
    );
  }
}
