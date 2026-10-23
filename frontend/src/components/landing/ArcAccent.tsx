const PATHS = {
  short: "M14 96C44 58 86 44 128 52",
  medium: "M14 96C58 30 132 20 196 58",
  long: "M14 96C52 18 142 8 236 78",
} as const;

export function ArcAccent({
  tone = "accent",
  length = "medium",
  flip = false,
  className = "",
}: {
  tone?: "ink" | "accent";
  length?: keyof typeof PATHS;
  flip?: boolean;
  className?: string;
}) {
  const colour = tone === "accent" ? "oklch(var(--accent))" : "oklch(var(--ink))";
  return (
    <svg
      // Flip via a class, not inline style: an inline transform would override any
      // rotate-* utility on the same element and silently drop the rotation.
      className={[className, flip ? "-scale-x-100" : ""].join(" ")}
      viewBox="0 0 240 120"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d={PATHS[length]}
        stroke={colour}
        strokeWidth="2.5"
        strokeLinecap="round"
        opacity={tone === "ink" ? 0.5 : 0.85}
      />
      <circle
        cx="14"
        cy="96"
        r="7"
        fill={colour}
        opacity={tone === "ink" ? 0.55 : 1}
      />
    </svg>
  );
}

/**
 * Soft concentric rings anchored off the left edge, so only their right arcs show.
 * Amber at low opacity: depth behind the headline, never a thing you look at.
 */
export function RingPattern({ className = "" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 400 400"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      {[70, 118, 166, 214].map((r, i) => (
        <circle
          key={r}
          cx="200"
          cy="200"
          r={r}
          stroke="oklch(var(--accent))"
          strokeWidth={i === 1 ? 2.5 : 1.5}
          opacity={0.42 - i * 0.07}
        />
      ))}
      <circle cx="200" cy="200" r="20" fill="oklch(var(--accent) / 0.16)" />
      <circle cx="200" cy="200" r="6" fill="oklch(var(--accent) / 0.7)" />
    </svg>
  );
}
