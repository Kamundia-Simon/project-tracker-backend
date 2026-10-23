import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type FloatingCardProps = {
  title?: string;
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
};

/**
 * A card in the hero illustration. Hidden from assistive tech: every one restates
 * something the page already says, and a screen reader hearing four unlabelled task
 * lists before the login button is worse off than one that hears none.
 */
export function FloatingCard({ title, icon, className, children }: FloatingCardProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "rounded-2xl border border-line bg-surface p-4",
        "shadow-[0_20px_45px_-28px_oklch(var(--ink)/0.45)]",
        // Decorative hover: the card lifts toward the reader and warms its edge.
        "transition-[transform,box-shadow,border-color] duration-200 ease-out",
        "hover:-translate-y-1 hover:border-amber/50 hover:shadow-[0_28px_60px_-28px_oklch(var(--ink)/0.5)]",
        className,
      )}
    >
      {(title || icon) && (
        <div className="mb-3 flex items-center gap-2">
          {icon}
          {title && <span className="text-[13px] font-semibold text-ink">{title}</span>}
        </div>
      )}
      {children}
    </div>
  );
}
