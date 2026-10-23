import { cn } from "@/lib/utils";

export function BrandLoader({
  size = 32,
  label = "Loading",
  className,
}: {
  size?: number;
  label?: string;
  className?: string;
}) {
  const dot = Math.round(size * 0.36);
  const gap = Math.round(size * 0.14);

  // Reading order in the grid; the travelling highlight runs clockwise through them.
  const dots = [
    { tone: "accent", delay: 0 },
    { tone: "ink", delay: 0.14 },
    { tone: "ink", delay: 0.42 },
    { tone: "ink", delay: 0.28 },
  ] as const;

  return (
    <span
      role="status"
      aria-live="polite"
      data-motion="essential"
      className={cn("inline-flex", className)}
    >
      <span
        className="grid grid-cols-2"
        style={{ gap, width: size, height: size }}
        aria-hidden="true"
      >
        {dots.map((d, i) => (
          <i
            key={i}
            className={cn(
              "animate-dot-wave block rounded-full",
              d.tone === "accent" ? "bg-accent" : "bg-ink",
            )}
            style={{ width: dot, height: dot, animationDelay: `${d.delay}s` }}
          />
        ))}
      </span>
      <span className="sr-only">{label}</span>
    </span>
  );
}

/** Full-page version, for route transitions and first paint. */
export function PageLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-svh items-center justify-center bg-canvas">
      <BrandLoader size={40} label={label} />
    </div>
  );
}
