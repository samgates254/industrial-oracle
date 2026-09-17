"use client";

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-control font-sans text-body font-medium transition-colors duration-fast ease-io disabled:pointer-events-none disabled:text-disabled focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus",
  {
    variants: {
      variant: {
        primary:
          "bg-brand text-inverse hover:bg-brand-strong disabled:bg-elevated",
        secondary:
          "bg-elevated text-primary border border-default hover:border-strong disabled:border-subtle",
        ghost: "bg-transparent text-secondary hover:bg-elevated hover:text-primary",
        critical:
          "bg-state-critical text-primary hover:brightness-110 disabled:bg-elevated",
        optimize:
          "border border-brand bg-brand-muted text-brand hover:bg-brand hover:text-inverse",
      },
      size: {
        sm: "h-7 px-2 text-meta",
        md: "h-control px-3",
        lg: "h-9 px-3.5",
      },
    },
    defaultVariants: {
      variant: "secondary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, type = "button", ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        type={asChild ? undefined : type}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export const IconButton = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, size = "md", ...props }, ref) => (
    <Button
      ref={ref}
      size={size}
      className={cn("px-0 aspect-square", className)}
      {...props}
    />
  ),
);
IconButton.displayName = "IconButton";

export { buttonVariants };
