import Link from "next/link";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { EmptyState } from "@/components/ui/feedback";
import { ArchitectureIntent } from "./architecture-intent";

export function PlaceholderScreen({
  title,
  group,
  summary,
  next,
  intent,
}: {
  title: string;
  group: string;
  summary: string;
  next?: string;
  intent?: {
    visual: string;
    not: string;
    stages: readonly string[];
  };
}) {
  return (
    <div className="io-page flex flex-col gap-section-gap">
      <div>
        <Breadcrumbs
          items={[
            { href: "/command", label: "Command" },
            { label: title },
          ]}
        />
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <h1 className="type-page-title">{title}</h1>
          <Badge tone="neutral">Foundation placeholder</Badge>
        </div>
        <p className="type-secondary mt-1">
          {group} · this route exists so navigation is real. The screen is not finished
          functionality.
        </p>
      </div>
      <Panel>
        <EmptyState
          title={`${title} is not implemented`}
          reason={summary}
        />
        {next ? <p className="type-meta text-muted">{next}</p> : null}
        {intent ? (
          <ArchitectureIntent
            visual={intent.visual}
            not={intent.not}
            stages={intent.stages}
          />
        ) : null}
        <div className="mt-4">
          <Button asChild variant="primary" size="sm">
            <Link href="/command">Return to Command Center</Link>
          </Button>
        </div>
      </Panel>
    </div>
  );
}
