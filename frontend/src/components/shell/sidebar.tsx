"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeft } from "lucide-react";
import { navGroups } from "./nav";
import { Wordmark } from "@/components/brand/mark";
import { IconButton } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import { useUiStore } from "@/stores/ui-store";

export function Sidebar() {
  const pathname = usePathname();
  const collapsed = useUiStore((s) => s.sidebarCollapsed);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const mobileNavOpen = useUiStore((s) => s.mobileNavOpen);
  const setMobileNavOpen = useUiStore((s) => s.setMobileNavOpen);

  return (
    <>
      {mobileNavOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-shell bg-overlay xl:hidden"
          aria-label="Close navigation"
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-shell flex flex-col border-r border-subtle bg-command transition-[width,transform] duration-base ease-io",
          collapsed ? "w-[56px]" : "w-[232px]",
          mobileNavOpen ? "translate-x-0" : "-translate-x-full xl:translate-x-0",
        )}
        aria-label="Primary"
      >
        <div className="flex h-12 items-center justify-between border-b border-subtle px-3">
          <Link href="/command" className="min-w-0" onClick={() => setMobileNavOpen(false)}>
            <Wordmark compact={collapsed} />
            <span className="sr-only">Industrial Oracle home</span>
          </Link>
          <IconButton
            variant="ghost"
            size="sm"
            className="hidden xl:inline-flex"
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
            onClick={toggleSidebar}
          >
            <PanelLeft className="h-4 w-4" />
          </IconButton>
        </div>
        <nav className="flex-1 overflow-y-auto py-3">
          {navGroups.map((group) => (
            <div key={group.id} className="mb-4">
              {collapsed ? (
                <p className="sr-only">{group.label}</p>
              ) : (
                <p className="type-panel px-3 pb-1.5">{group.label}</p>
              )}
              <ul className="flex flex-col gap-0.5 px-2">
                {group.items.map((item) => {
                  const active =
                    pathname === item.href || pathname.startsWith(`${item.href}/`);
                  const Icon = item.icon;
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        title={item.label}
                        onClick={() => setMobileNavOpen(false)}
                        className={cn(
                          "flex items-center gap-2 rounded-control px-2 py-1.5 text-body transition-colors duration-fast",
                          active
                            ? "bg-elevated text-primary shadow-[inset_2px_0_0_0_var(--io-brand)]"
                            : "text-secondary hover:bg-elevated hover:text-primary",
                        )}
                        aria-current={active ? "page" : undefined}
                      >
                        <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                        {collapsed ? (
                          <span className="sr-only">{item.label}</span>
                        ) : (
                          <>
                            <span className="min-w-0 flex-1 truncate">{item.label}</span>
                            {item.status === "foundation" ? (
                              <span className="type-status text-muted">WIP</span>
                            ) : null}
                          </>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
}
