"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";
import { IconButton } from "./button";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;
export const DialogClose = DialogPrimitive.Close;

export function DialogContent({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-overlay bg-overlay" />
      <DialogPrimitive.Content
        className={cn(
          "fixed left-1/2 top-1/2 z-modal w-[min(560px,calc(100vw-24px))] -translate-x-1/2 -translate-y-1/2 rounded-modal border border-default bg-modal p-4 shadow-overlay",
          className,
        )}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            <DialogPrimitive.Title className="type-section">{title}</DialogPrimitive.Title>
            {description ? (
              <DialogPrimitive.Description className="type-secondary mt-1">
                {description}
              </DialogPrimitive.Description>
            ) : (
              <DialogPrimitive.Description className="sr-only">
                {title}
              </DialogPrimitive.Description>
            )}
          </div>
          <DialogPrimitive.Close asChild>
            <IconButton variant="ghost" aria-label="Close" size="sm">
              <X className="h-4 w-4" />
            </IconButton>
          </DialogPrimitive.Close>
        </div>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
