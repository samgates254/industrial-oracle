"use client";

import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { cn } from "@/lib/cn";

export const Dropdown = DropdownMenu.Root;
export const DropdownTrigger = DropdownMenu.Trigger;

export function DropdownContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <DropdownMenu.Portal>
      <DropdownMenu.Content
        sideOffset={6}
        align="end"
        className={cn(
          "z-modal min-w-[12rem] rounded-control border border-default bg-modal p-1 shadow-overlay",
          className,
        )}
      >
        {children}
      </DropdownMenu.Content>
    </DropdownMenu.Portal>
  );
}

export function DropdownItem({
  children,
  onSelect,
}: {
  children: React.ReactNode;
  onSelect?: () => void;
}) {
  return (
    <DropdownMenu.Item
      onSelect={onSelect}
      className="cursor-pointer rounded-control px-2 py-1.5 text-body text-primary outline-none data-[highlighted]:bg-elevated"
    >
      {children}
    </DropdownMenu.Item>
  );
}
