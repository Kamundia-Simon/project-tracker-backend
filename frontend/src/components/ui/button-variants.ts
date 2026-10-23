/** Button class variants, split out so button.tsx exports only a component (react-refresh). */
import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  "group/button relative inline-flex shrink-0 items-center justify-center rounded-md border border-transparent bg-clip-padding text-[13px] font-medium whitespace-nowrap transition-[background-color,border-color,color] duration-150 ease-out select-none active:scale-[.98] disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        // Filled accent = action. The one primary button in the app.
        default: "bg-accent text-accent-ink hover:brightness-[0.97]",
        outline:
          "border-line-strong bg-surface hover:bg-surface-2 hover:border-ink-faint",
        secondary: "bg-surface-3 text-ink hover:bg-line",
        ghost: "hover:bg-surface-3",
        destructive: "bg-danger/10 text-danger hover:bg-danger/20",
        link: "text-accent-strong underline-offset-4 hover:underline",
      },
      size: {
        // 34px desktop, 44px minimum on touch (docs/mockups/README.md).
        default: "h-11 gap-1.5 px-3.5 md:h-[34px]",
        sm: "h-11 gap-1 px-3 text-xs md:h-[30px]",
        lg: "h-12 gap-2 px-4 text-sm md:h-[38px]",
        icon: "size-11 md:size-[34px]",
        "icon-sm": "size-11 md:size-[30px]",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);
