"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";
import { IconButton } from "./button";

export const Drawer = DialogPrimitive.Root;
export const DrawerTrigger = DialogPrimitive.Trigger;

export function DrawerContent({
  title,
  children,
  className,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-overlay bg-overlay" />
      <DialogPrimitive.Content
        className={cn(
          "fixed inset-y-0 right-0 z-modal flex w-[min(420px,100vw)] flex-col border-l border-default bg-modal shadow-overlay",
          className,
        )}
      >
        <header className="flex h-12 items-center justify-between border-b border-subtle px-4">
          <DialogPrimitive.Title className="type-section">{title}</DialogPrimitive.Title>
          <DialogPrimitive.Description className="sr-only">
            {title} inspection panel
          </DialogPrimitive.Description>
          <DialogPrimitive.Close asChild>
            <IconButton variant="ghost" aria-label="Close panel" size="sm">
              <X className="h-4 w-4" />
            </IconButton>
          </DialogPrimitive.Close>
        </header>
        <div className="flex-1 overflow-auto p-4">{children}</div>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
