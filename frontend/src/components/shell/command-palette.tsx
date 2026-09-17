"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Dialog } from "@/components/ui/dialog";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Input } from "@/components/ui/input";
import { allNavItems, extraRoutes } from "./nav";
import { useUiStore } from "@/stores/ui-store";
import { cn } from "@/lib/cn";

export function CommandPalette() {
  const open = useUiStore((s) => s.commandPaletteOpen);
  const setOpen = useUiStore((s) => s.setCommandPaletteOpen);
  const [query, setQuery] = useState("");
  const router = useRouter();

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    const items = [...allNavItems, ...extraRoutes];
    if (!q) return items;
    return items.filter(
      (item) =>
        item.label.toLowerCase().includes(q) || item.href.toLowerCase().includes(q),
    );
  }, [query]);

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setQuery("");
      }}
    >
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-overlay bg-overlay" />
        <DialogPrimitive.Content className="fixed left-1/2 top-[18%] z-modal w-[min(520px,calc(100vw-24px))] -translate-x-1/2 rounded-modal border border-default bg-modal shadow-overlay">
          <DialogPrimitive.Title className="sr-only">Command palette</DialogPrimitive.Title>
          <DialogPrimitive.Description className="sr-only">
            Search screens and navigate Industrial Oracle
          </DialogPrimitive.Description>
          <div className="border-b border-subtle p-2">
            <Input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search screens, assets, orders…"
              aria-label="Search"
            />
          </div>
          <ul className="max-h-72 overflow-auto p-1">
            {results.length === 0 ? (
              <li className="px-3 py-4 type-secondary">No matching screens.</li>
            ) : (
              results.map((item) => (
                <li key={item.href}>
                  <button
                    type="button"
                    className={cn(
                      "flex w-full items-center justify-between rounded-control px-3 py-2 text-left text-body text-primary hover:bg-elevated",
                    )}
                    onClick={() => {
                      router.push(item.href);
                      setOpen(false);
                      setQuery("");
                    }}
                  >
                    <span>{item.label}</span>
                    <span className="type-ident text-muted">{item.href}</span>
                  </button>
                </li>
              ))
            )}
          </ul>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </Dialog>
  );
}
