"use client";

import { useEffect } from "react";
import { useUiStore } from "@/stores/ui-store";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { CommandPalette } from "./command-palette";
import { cn } from "@/lib/cn";

export function AppShell({ children }: { children: React.ReactNode }) {
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const density = useUiStore((s) => s.density);
  const setCommandPaletteOpen = useUiStore((s) => s.setCommandPaletteOpen);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setCommandPaletteOpen]);

  return (
    <div data-density={density} className="min-h-screen bg-app">
      <Sidebar />
      <div
        className={cn(
          "flex min-h-screen flex-col transition-[padding] duration-base ease-io",
          collapsed ? "xl:pl-[56px]" : "xl:pl-[232px]",
        )}
      >
        <Topbar />
        <main id="main" className="flex-1">
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}
