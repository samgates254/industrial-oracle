"use client";

import * as Popover from "@radix-ui/react-popover";
import { Bell } from "lucide-react";
import { commandCenterDemo } from "@/lib/demo";
import { getDataSource } from "@/lib/api/client";
import { AlertItem } from "@/components/industrial/alerts";
import { IconButton } from "@/components/ui/button";
import { useUiStore } from "@/stores/ui-store";
import Link from "next/link";

export function AlertCenter() {
  const open = useUiStore((s) => s.alertCenterOpen);
  const setOpen = useUiStore((s) => s.setAlertCenterOpen);
  const demoMode = getDataSource() === "demo";
  const alerts = demoMode ? commandCenterDemo.alerts : [];
  const unacked = alerts.filter((a) => !a.acknowledged).length;

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <IconButton
          variant="ghost"
          aria-label={unacked ? `${unacked} unacknowledged alerts` : "Alerts"}
        >
          <span className="relative">
            <Bell className="h-4 w-4" />
            {unacked > 0 ? (
              <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-state-warning" />
            ) : null}
          </span>
        </IconButton>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="z-modal w-[min(380px,calc(100vw-24px))] rounded-modal border border-default bg-modal p-3 shadow-overlay"
        >
          <div className="mb-2 flex items-center justify-between">
            <p className="type-section">Alert center</p>
            <Link href="/alerts" className="type-meta text-brand">
              Open queue
            </Link>
          </div>
          {alerts.length === 0 ? (
            <p className="type-meta text-secondary">
              {demoMode
                ? "No demo alerts."
                : "API mode: alerts are on Command Center from projected constraints. This bell does not invent demo alerts."}
            </p>
          ) : (
            alerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                timeZone={commandCenterDemo.meta.plant.timezone}
              />
            ))
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
