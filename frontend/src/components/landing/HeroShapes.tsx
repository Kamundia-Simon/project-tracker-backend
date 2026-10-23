/**
 * The flowing shapes behind the hero. One SVG, sliced to fill whatever box it is
 * given, so the curves scale without pixelation and without a second asset.
 * Three colours doing three jobs: amber carries the movement, black anchors the
 * right edge and gives the composition weight, white keeps it from closing in.
 */
export function HeroShapes({ className = "" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 760 900"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
      focusable="false"
    >
      {/* Widest, faintest layer — sets the silhouette of the whole right side. */}
      <path
        d="M214 -40c96 158-40 268 56 404s318 158 348 348c12 76-8 148-38 188h180V-40Z"
        fill="oklch(var(--accent) / 0.10)"
      />

      {/* Black ribbon, furthest back of the two solids: the depth layer. */}
      <path
        d="M560 -40c-96 150 46 262-34 404-74 130-96 310-30 536h130c-74-226-40-400 34-534 82-148-66-256 30-406Z"
        fill="oklch(var(--ink))"
      />

      {/* Amber ribbon, offset from the black one so both edges stay visible. */}
      <path
        d="M470 -40c-84 162 60 266-20 408-74 132-100 318-40 532h128c-66-216-34-392 40-526 80-146-62-252 22-414Z"
        fill="oklch(var(--accent))"
      />

      {/* A second, smaller black curl near the top right for asymmetry. */}
      <path
        d="M700 -20c-44 118 18 206 60 280V-20Z"
        fill="oklch(var(--ink) / 0.9)"
      />

      {/* Hairline echo, carrying the curve back across the empty lower half. */}
      <path
        d="M90 620c156-62 258 40 310 152 30 66 78 116 144 144"
        fill="none"
        stroke="oklch(var(--accent) / 0.5)"
        strokeWidth="2"
      />
      <circle cx="90" cy="620" r="5" fill="oklch(var(--accent))" />
    </svg>
  );
}
