"use client";

import { Menu, Radio, Search } from "lucide-react";
import { commandCenterDemo } from "@/lib/demo";
import { Select } from "@/components/ui/select";
import { IconButton } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { useSessionStore } from "@/stores/session-store";
import { useUiStore } from "@/stores/ui-store";
import { AlertCenter } from "./alert-center";

const connectivityState = {
  live: "success",
  degraded: "degraded",
  offline: "offline",
  synthetic: "degraded",
} as const;

export function Topbar() {
  const user = useSessionStore((s) => s.user);
  const setMobileNavOpen = useUiStore((s) => s.setMobileNavOpen);
  const setCommandPaletteOpen = useUiStore((s) => s.setCommandPaletteOpen);
  const density = useUiStore((s) => s.density);
  const setDensity = useUiStore((s) => s.setDensity);
  const meta = commandCenterDemo.meta;

  return (
    <header className="flex h-12 items-center gap-3 border-b border-subtle bg-command px-3">
      <IconButton
        variant="ghost"
        className="xl:hidden"
        aria-label="Open navigation"
        onClick={() => setMobileNavOpen(true)}
      >
        <Menu className="h-4 w-4" />
      </IconButton>

      <Select
        ariaLabel="Organization"
        value={meta.organization.id}
        onValueChange={() => undefined}
        items={[
          { value: meta.organization.id, label: meta.organization.code },
        ]}
      />
      <Select
        ariaLabel="Plant"
        value={meta.plant.id}
        onValueChange={() => undefined}
        items={[{ value: meta.plant.id, label: meta.plant.code }]}
      />

      <IconButton
        variant="ghost"
        className="xl:hidden"
        aria-label="Open search"
        onClick={() => setCommandPaletteOpen(true)}
      >
        <Search className="h-4 w-4" />
      </IconButton>
      <button
        type="button"
        onClick={() => setCommandPaletteOpen(true)}
        className="hidden h-control min-w-0 flex-1 items-center gap-2 rounded-control border border-default bg-elevated px-2 text-left text-secondary xl:flex"
        aria-label="Open search"
      >
        <Search className="h-3.5 w-3.5" />
        <span className="type-body truncate">Search screens, assets, orders</span>
        <kbd className="ml-auto type-ident text-muted">Ctrl K</kbd>
      </button>

      <div className="ml-auto flex items-center gap-2">
        <span className="hidden items-center gap-1.5 type-meta text-secondary xl:inline-flex">
          <Radio className="h-3 w-3 text-data-telemetry" aria-hidden />
          {meta.shift.name}
        </span>
        <StatusIndicator
          state={connectivityState[meta.connectivity]}
          label={meta.connectivity === "live" ? "Connected" : meta.connectivity}
          className="hidden xl:inline-flex"
        />
        <Select
          ariaLabel="Density"
          value={density}
          onValueChange={(v) => setDensity(v as "compact" | "comfortable")}
          items={[
            { value: "compact", label: "Dense" },
            { value: "comfortable", label: "Comfort" },
          ]}
          className="hidden min-w-[7.5rem] xl:inline-flex"
        />
        <AlertCenter />
        <div className="hidden items-center gap-2 border-l border-subtle pl-2 xl:flex">
          <div className="text-right">
            <p className="type-meta text-primary">{user.name}</p>
            <p className="type-meta text-muted">{user.role}</p>
          </div>
          <Badge tone="demo">Demo</Badge>
        </div>
      </div>
    </header>
  );
}
