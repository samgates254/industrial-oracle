"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-control w-full rounded-control border border-default bg-elevated px-2.5 text-body text-primary placeholder:text-muted",
        "focus-visible:border-focus",
        "disabled:text-disabled",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
