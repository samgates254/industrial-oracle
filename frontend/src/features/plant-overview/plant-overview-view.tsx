"use client";

import { useMemo, useState } from "react";
import type { PlantTopologySnapshot } from "@/types/topology";
import { AlertBanner } from "@/components/industrial/alerts";
import { IntelligenceStack } from "@/components/industrial/intelligence";
import { StatusRail } from "@/components/industrial/status-rail";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Drawer, DrawerContent } from "@/components/ui/drawer";
import { formatTimestamp } from "@/lib/format";
import { PlantStatusStrip } from "./plant-status-strip";
import { PlantTopology } from "./plant-topology";
import { TopologyDetail } from "./topology-detail";
import { ImpactChain } from "./impact-chain";
import { MobileFlow } from "./mobile-flow";

export function PlantOverviewView({ snapshot }: { snapshot: PlantTopologySnapshot }) {
  const [selectedId, setSelectedId] = useState<string | null>(
    snapshot.sequence[0] ?? snapshot.nodes[0]?.id ?? null,
  );
  const [drawerOpen, setDrawerOpen] = useState(false);
  const selected = useMemo(
    () => snapshot.nodes.find((node) => node.id === selectedId) ?? null,
    [snapshot.nodes, selectedId],
  );

  function selectNode(id: string) {
    setSelectedId(id);
    if (
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 1279px)").matches
    ) {
      setDrawerOpen(true);
    }
  }

  return (
    <div className="io-page flex flex-col gap-5">
      {snapshot.meta.source === "demo" ? (
        <p className="type-meta text-muted" role="status">
          {snapshot.meta.disclaimer}
        </p>
      ) : null}

      <header>
        <Breadcrumbs
          items={[
            { href: "/command", label: "Command" },
            { label: "Plant" },
          ]}
        />
        <h1 className="type-page-title mt-1">Plant Overview</h1>
        <p className="type-secondary mt-1">
          {snapshot.meta.plant.name} · {snapshot.meta.shift.name}
        </p>
      </header>

      <StatusRail
        items={[
          { label: "Plant", value: snapshot.health.status, state: snapshot.health.status },
          { label: "Shift", value: snapshot.meta.shift.name },
          {
            label: "Link",
            value: snapshot.meta.connectivity === "live" ? "Connected" : snapshot.meta.connectivity,
            state: snapshot.meta.connectivity === "live" ? "success" : "offline",
          },
          {
            label: "Snapshot",
            value: formatTimestamp(snapshot.meta.snapshotAt, snapshot.meta.plant.timezone),
          },
        ]}
      />

      <p className="type-body text-secondary">{snapshot.health.summary}</p>

      <AlertBanner alerts={snapshot.alerts} />

      <PlantStatusStrip counts={snapshot.counts} />

      <MobileFlow snapshot={snapshot} selectedId={selectedId} onSelect={selectNode} />

      <div className="hidden md:block">
        <PlantTopology
          snapshot={snapshot}
          selectedId={selectedId}
          onSelect={selectNode}
        />
      </div>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)]">
        <ImpactChain impacts={snapshot.impact} />
        <section className="hidden io-zone py-3 xl:block">
          <TopologyDetail
            node={selected}
            bottleneck={snapshot.bottleneck}
            onClear={() => setSelectedId(null)}
          />
        </section>
      </div>

      <div className="xl:hidden">
        <Drawer
          open={drawerOpen}
          onOpenChange={(open) => {
            setDrawerOpen(open);
          }}
        >
          <DrawerContent title={selected?.name ?? "Node"}>
            <TopologyDetail
              node={selected}
              bottleneck={snapshot.bottleneck}
              onClear={() => {
                setDrawerOpen(false);
                setSelectedId(null);
              }}
            />
          </DrawerContent>
        </Drawer>
      </div>

      <IntelligenceStack
        blocks={snapshot.intelligence}
        kinds={["optimization-result", "ai-interpretation"]}
      />
    </div>
  );
}
