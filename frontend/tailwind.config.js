/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      colors: {
        background: "oklch(var(--background) / <alpha-value>)",
        foreground: "oklch(var(--foreground) / <alpha-value>)",
        card: {
          DEFAULT: "oklch(var(--card) / <alpha-value>)",
          foreground: "oklch(var(--card-foreground) / <alpha-value>)",
        },
        popover: {
          DEFAULT: "oklch(var(--popover) / <alpha-value>)",
          foreground: "oklch(var(--popover-foreground) / <alpha-value>)",
        },
        primary: {
          DEFAULT: "oklch(var(--primary) / <alpha-value>)",
          foreground: "oklch(var(--primary-foreground) / <alpha-value>)",
        },
        secondary: {
          DEFAULT: "oklch(var(--secondary) / <alpha-value>)",
          foreground: "oklch(var(--secondary-foreground) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "oklch(var(--muted) / <alpha-value>)",
          foreground: "oklch(var(--muted-foreground) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "oklch(var(--accent) / <alpha-value>)",
          foreground: "oklch(var(--accent-foreground) / <alpha-value>)",
        },
        destructive: {
          DEFAULT: "oklch(var(--destructive) / <alpha-value>)",
        },
        border: "var(--border)",
        input: "var(--input)",
        ring: "oklch(var(--ring) / <alpha-value>)",
        // 3Gem tokens — see docs/design-tokens.md. Named by role, never by hue.
        ink: {
          DEFAULT: "oklch(var(--ink) / <alpha-value>)",
          muted: "oklch(var(--ink-muted) / <alpha-value>)",
          faint: "oklch(var(--ink-faint) / <alpha-value>)",
        },
        canvas: "oklch(var(--canvas) / <alpha-value>)",
        surface: {
          DEFAULT: "oklch(var(--surface) / <alpha-value>)",
          2: "oklch(var(--surface-2) / <alpha-value>)",
          3: "oklch(var(--surface-3) / <alpha-value>)",
        },
        line: {
          DEFAULT: "oklch(var(--line) / <alpha-value>)",
          strong: "oklch(var(--line-strong) / <alpha-value>)",
        },
        amber: {
          DEFAULT: "oklch(var(--amber) / <alpha-value>)",
          strong: "oklch(var(--amber-strong) / <alpha-value>)",
          ink: "oklch(var(--amber-ink) / <alpha-value>)",
        },
        ok: "oklch(var(--ok) / <alpha-value>)",
        warn: "oklch(var(--warn) / <alpha-value>)",
        danger: "oklch(var(--danger) / <alpha-value>)",
        chart: {
          "1": "oklch(var(--chart-1) / <alpha-value>)",
          "2": "oklch(var(--chart-2) / <alpha-value>)",
          "3": "oklch(var(--chart-3) / <alpha-value>)",
          "4": "oklch(var(--chart-4) / <alpha-value>)",
          "5": "oklch(var(--chart-5) / <alpha-value>)",
        },
        sidebar: {
          DEFAULT: "oklch(var(--sidebar) / <alpha-value>)",
          foreground: "oklch(var(--sidebar-foreground) / <alpha-value>)",
          primary: "oklch(var(--sidebar-primary) / <alpha-value>)",
          "primary-foreground": "oklch(var(--sidebar-primary-foreground) / <alpha-value>)",
          accent: "oklch(var(--sidebar-accent) / <alpha-value>)",
          "accent-foreground": "oklch(var(--sidebar-accent-foreground) / <alpha-value>)",
          border: "var(--sidebar-border)",
          ring: "oklch(var(--sidebar-ring) / <alpha-value>)",
        },
      },
    },
  },
  plugins: [],
}

