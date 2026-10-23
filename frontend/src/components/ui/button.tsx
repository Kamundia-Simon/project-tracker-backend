import * as React from "react";
import { type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";

import { cn } from "@/lib/utils";
import { BrandLoader } from "@/components/BrandLoader";
import { buttonVariants } from "@/components/ui/button-variants";

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  loading = false,
  disabled,
  children,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
    loading?: boolean;
  }) {
  const Comp = asChild ? Slot.Root : "button";

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      aria-busy={loading || undefined}
      disabled={disabled || loading}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    >
      {/* Hidden rather than replaced, so the button keeps its width and the label keeps
          focus while loading (frontend-standards.md §7). */}
      <span
        className={cn(
          "inline-flex items-center gap-1.5",
          loading && "invisible",
        )}
      >
        {children}
      </span>
      {loading && (
        <span className="absolute inset-0 grid place-items-center">
          <BrandLoader size={16} label="Working" />
        </span>
      )}
    </Comp>
  );
}

export { Button, buttonVariants };
