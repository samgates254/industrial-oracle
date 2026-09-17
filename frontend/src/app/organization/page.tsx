import type { Metadata } from "next";
import Link from "next/link";
import { Wordmark } from "@/components/brand/mark";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { commandCenterDemo } from "@/lib/demo";

export const metadata: Metadata = { title: "Organization" };

export default function OrganizationPage() {
  const org = commandCenterDemo.meta.organization;
  const plant = commandCenterDemo.meta.plant;

  return (
    <div className="min-h-screen bg-command">
      <header className="flex h-12 items-center justify-between border-b border-subtle px-4">
        <Wordmark />
        <Badge tone="demo">Synthetic context</Badge>
      </header>
      <main id="main" className="mx-auto max-w-3xl io-page">
        <h1 className="type-page-title">Select operating context</h1>
        <p className="type-secondary mt-2">
          Organization and plant selection will be backed by the directory API. Phase 1
          exposes the demo context only.
        </p>
        <div className="mt-6 io-grid">
          <Panel>
            <p className="type-panel">{org.code}</p>
            <h2 className="type-section mt-1">{org.name}</h2>
            <p className="type-body mt-3">{plant.name}</p>
            <p className="type-ident mt-1 text-muted">{plant.timezone}</p>
            <div className="mt-4">
              <Button asChild variant="primary" size="sm">
                <Link href="/command">Open Plant 01 command center</Link>
              </Button>
            </div>
          </Panel>
        </div>
      </main>
    </div>
  );
}
