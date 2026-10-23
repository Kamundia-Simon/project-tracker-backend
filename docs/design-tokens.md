# Design tokens

Decided 2026-08-25, during frontend scaffolding.

- **Base primitives:** Radix UI (see reasoning in chat — maturity/documentation over Base UI's newer, thinner ecosystem)
- **shadcn style preset:** Mira — "dense and product-focused" (shadcncraft.com's own description), a good structural fit for a queue/table/checklist-heavy workflow app
- **Icon library:** Phosphor Icons (leaning choice, not yet run) — multiple weights (outline/fill/duotone) let the same icon express state (checklist item pending vs. done, health on-track/at-risk/overdue) without relying on color alone. Trade-off: less copy-paste compatible with shadcn's own Lucide-based docs, and a minor inconsistency with `Cpi-Dashboard`'s Lucide icons — accepted deliberately.
- **Theme preset ID:** `b7X65jeZhR` (shadcncraft), applied via `npx shadcn@latest apply --preset b7X65jeZhR`. Warm/amber-toned light theme, full dark mode + sidebar + chart token set included, `--radius: 0.875rem` (fairly rounded corners).

## Token reference (light / dark)

Applied via the CLI command above — recorded here so the exact values survive even if the CLI/preset changes later.

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.147 0.004 49.3);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.147 0.004 49.3);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.147 0.004 49.3);
  --primary: oklch(0.852 0.199 91.936);
  --primary-foreground: oklch(0.421 0.095 57.708);
  --secondary: oklch(0.967 0.001 286.375);
  --secondary-foreground: oklch(0.21 0.006 285.885);
  --muted: oklch(0.96 0.002 17.2);
  --muted-foreground: oklch(0.547 0.021 43.1);
  --accent: oklch(0.96 0.002 17.2);
  --accent-foreground: oklch(0.214 0.009 43.1);
  --destructive: oklch(0.577 0.245 27.325);
  --border: oklch(0.922 0.005 34.3);
  --input: oklch(0.922 0.005 34.3);
  --ring: oklch(0.714 0.014 41.2);
  --chart-1: oklch(0.868 0.007 39.5);
  --chart-2: oklch(0.547 0.021 43.1);
  --chart-3: oklch(0.438 0.017 39.3);
  --chart-4: oklch(0.367 0.016 35.7);
  --chart-5: oklch(0.268 0.011 36.5);
  --radius: 0.875rem;
  --sidebar: oklch(0.986 0.002 67.8);
  --sidebar-foreground: oklch(0.147 0.004 49.3);
  --sidebar-primary: oklch(0.681 0.162 75.834);
  --sidebar-primary-foreground: oklch(0.987 0.026 102.212);
  --sidebar-accent: oklch(0.96 0.002 17.2);
  --sidebar-accent-foreground: oklch(0.214 0.009 43.1);
  --sidebar-border: oklch(0.922 0.005 34.3);
  --sidebar-ring: oklch(0.714 0.014 41.2);
}

.dark {
  --background: oklch(0.147 0.004 49.3);
  --foreground: oklch(0.986 0.002 67.8);
  --card: oklch(0.214 0.009 43.1);
  --card-foreground: oklch(0.986 0.002 67.8);
  --popover: oklch(0.214 0.009 43.1);
  --popover-foreground: oklch(0.986 0.002 67.8);
  --primary: oklch(0.795 0.184 86.047);
  --primary-foreground: oklch(0.421 0.095 57.708);
  --secondary: oklch(0.274 0.006 286.033);
  --secondary-foreground: oklch(0.985 0 0);
  --muted: oklch(0.268 0.011 36.5);
  --muted-foreground: oklch(0.714 0.014 41.2);
  --accent: oklch(0.268 0.011 36.5);
  --accent-foreground: oklch(0.986 0.002 67.8);
  --destructive: oklch(0.704 0.191 22.216);
  --border: oklch(1 0 0 / 10%);
  --input: oklch(1 0 0 / 15%);
  --ring: oklch(0.547 0.021 43.1);
  --chart-1: oklch(0.868 0.007 39.5);
  --chart-2: oklch(0.547 0.021 43.1);
  --chart-3: oklch(0.438 0.017 39.3);
  --chart-4: oklch(0.367 0.016 35.7);
  --chart-5: oklch(0.268 0.011 36.5);
  --sidebar: oklch(0.214 0.009 43.1);
  --sidebar-foreground: oklch(0.986 0.002 67.8);
  --sidebar-primary: oklch(0.795 0.184 86.047);
  --sidebar-primary-foreground: oklch(0.987 0.026 102.212);
  --sidebar-accent: oklch(0.268 0.011 36.5);
  --sidebar-accent-foreground: oklch(0.986 0.002 67.8);
  --sidebar-border: oklch(1 0 0 / 10%);
  --sidebar-ring: oklch(0.547 0.021 43.1);
}
```

**How to apply:** whenever building or mocking Project-Tracker UI (real frontend code or a quick visualize-tool mockup), use these tokens rather than a generic/placeholder palette, so everything stays visually consistent with what's actually installed in the app.

---

## Resolutions required by `frontend-standards.md` (2026-10-15)

The preset above was chosen before the frontend standard was written. Four things in it conflict with that standard, and the standard wins in each case — recorded here with the reasoning, because each one is a change to values the CLI generated and would otherwise look like drift.

### 1. The amber collision — resolved by form, not by hue (settled 2026-10-16)

`--primary` is amber, and the status vocabulary makes **amber mean "needs attention / at risk / pending"**. Both on one screen trains the user to read amber as decoration, which is the signal the dashboard depends on.

My first resolution was *status wins, brand yields* — near-black buttons, amber confined to the active indicator and focus ring. The refined mockups (`docs/mockups/`) took a different route and it is the better one:

**Resolution: amber as a filled surface means action; amber as text on a 6–7% tint means status.** They never share a form. A primary button is `background: var(--accent)` with near-black ink; a warning badge is `color: var(--amber)` with a `currentColor` border and dot on a near-transparent tint, and is never filled. The two ambers also differ in lightness — `--accent` `#d9a72e` is a bright gold, `--amber` `#8f5600` a dark ochre only ever used as ink — so they don't read as the same colour even side by side.

This keeps the brand visible, which the all-neutral version lost. It depends on the rule holding absolutely: **no filled amber badges, no outlined amber buttons.** The moment a status is filled amber, the distinction collapses and the first resolution becomes the fallback.

**Confirmed absolute, with no exceptions, 2026-10-21.** The case tested was the selected filter chip, which the mockups fill with amber. A pressed chip is arguably a control rather than a status, and the contrast is fine (8.04:1) — but it would put filled amber on the same screen as amber status text two rows below, which is the exact eye-training problem this resolution exists to prevent. **Selected chips are `--text` fill with `--bg` ink.** Amber fill is reserved for action buttons. The rule's whole value is that it has none of these exceptions, so a borderline case that is merely defensible is not enough to open one.

### 2. Radius — reverted upward (settled 2026-10-16)

I had dropped `--radius` to `0.5rem`, on the reasoning that 14px on everything reads as a consumer landing page.

**Resolution: a scale, with the preset's generosity kept for panels.** 9px controls · 14px panels · 16px hero · 999px status pills and chips. The refined mockups demonstrate that the original 14px works once it is a *scale* rather than one value: controls noticeably tighter than their containers is what reads as deliberate, and it was the uniformity, not the radius itself, that made the preset look generic. Pill shape stays reserved for status and filter chips.

### 3. Missing semantic status tokens

The preset ships `--destructive` plus five chart colours and no success, warning or info. Status badges would therefore be improvised per component — the exact failure the standard exists to prevent.

**Resolution: add `--success`, `--warning`, `--info` and `--neutral`** (plus foregrounds), in both themes, as first-class tokens beside `--destructive`. `--destructive` stays as the token for destructive *actions*; `--danger` for the overdue/blocked *state* may alias it, but they are referenced by their own names so the two meanings can diverge later.

The chart tokens are a monochrome warm ramp, which is fine for distribution charts and useless for status. Do not reach for `--chart-3` because it happens to look right.

### 4. Monospace face

Not covered by the preset. The standard calls for mono on RDR numbers, IDs, timestamps and numeric data, where consistent digit width makes a column scannable and a transposed digit visible.

**Resolution: IBM Plex Mono**, self-hosted or via the font stack, scoped narrowly — numerals and identifiers only, never body text, labels or headings. Mono is a tool for alignment, not a style.

## Canonical token values (from `docs/mockups/`, 2026-10-16)

The hex values below are what the agreed mockups use and are the source for Slice 0b. They need converting to the bare-OKLCH-component format the preset already uses in `src/index.css`, mapped through `tailwind.config.js` — not added as a parallel hex system.

```css
:root {
  color-scheme: light;
  --bg: #f6f6f4;            /* page ground */
  --surface: #ffffff;       /* panel */
  --surface-2: #fafaf8;     /* hover, inset fill */
  --surface-3: #f1f1ee;     /* track, avatar well */
  --line: #e4e4df;          /* resting border */
  --line-strong: #d4d4cd;   /* hover border, control border */
  --text: #171715;
  --muted: #62625d;         /* secondary content, read — 6.13:1 */
  --faint: #70706a;         /* metadata — 4.5:1 even on --surface-3; only on --surface and --surface-2 */
  --accent: #fbc804;        /* official 3Gem amber, from 3gem.com. Fill only — 1.57:1, never text */
  --accent-strong: #8f6200; /* brand ink + focus ring — 5.2:1 */
  --accent-ink: #201700;    /* text on an --accent fill — 8.04:1 */
  --focus: rgba(217,167,46,.22);  /* decorative inner glow ONLY, never the indicator */
  --green: #1b724d;  --amber: #8f5600;  --red: #bb3744;
  /* --blue exists but is NOT a status colour — see "Blue" below */
  --blue: #305f99;
  --shadow: 0 10px 28px rgba(24,24,20,.06);
  --topbar: rgba(255,255,255,.88);
  --rail: #f1f1ee;
  --r: 14px;
}

:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #11110f;  --surface: #191917;  --surface-2: #1e1e1b;  --surface-3: #262622;
  --line: #30302c;  --line-strong: #3d3d37;
  --text: #f2f2ed;  --muted: #b1b1a8;  --faint: #8b8b82;  /* was #7d7d74, 3.66:1 on --surface-3 */
  --accent: #ffdd6b;  --accent-strong: #f0c55b;
  --focus: rgba(227,180,65,.18);
  --green: #55b98a;  --amber: #dda84c;  --red: #df6b74;  --blue: #78a2d6;
  --shadow: 0 14px 34px rgba(0,0,0,.22);
  --topbar: rgba(25,25,23,.90);
  --rail: #151513;
}
```

**Corrected twice after contrast audits** (2026-10-21, then 2026-10-22 when a second pass showed `--faint` had only ever been checked against white). The values above are the ones **shipped in `docs/mockups/`** and are authoritative.

Two of the corrections are worth remembering as rules rather than values:

- **`--faint` is only legal on `--surface` and `--surface-2`.** At `#70706a` it clears 4.5:1 on those; the sidebar (`--rail` / `--surface-3`) and the page ground are darker, so metadata there uses `--muted`. A token that passes on white does not pass everywhere — check each ground it actually lands on.
- **`--accent` is a fill, never a text or lone-indicator colour.** At 2.2:1 it fails the 3:1 non-text minimum. It is legitimate as a *redundant* marker — the sidebar's active bar and the tab underline sit beside a weight and background change that already carry the state — but never as the only signal. The pipeline's current-step rail was changed to `--accent-strong` for exactly this reason: there it was the signal.

### The official brand amber (settled 2026-10-22)

`--accent` was `#d9a72e`, a value derived from the shadcn preset. It is now **`#ffd34e`, taken from the 3Gem logo artwork** (`Cpi-Dashboard/frontend/public/favicon.svg`, reused here as `public/brand/3gem-mark.svg`). The old value was never the brand's; it merely looked plausible, and the mismatch only became obvious once the real logo sat next to a button.

This makes the fill-only rule *stricter*, not looser: at `#fbc804` the accent is **1.57:1** against white, so it fails the 3:1 non-text minimum by a wider margin than before. It is legitimate as a filled surface with `--accent-ink` on top, and nowhere else. Focus rings, links and any amber that carries meaning stay on `--accent-strong` (`#8f6200`).

The artboards in `docs/mockups/` still carry the old value in their own `:root` blocks. The token table here wins; they should be updated when next touched.

### Blue is not a status colour (settled 2026-10-22)

`--blue` exists in the palette but has **no place in the status vocabulary**, which is exactly four: green, amber, red, neutral grey. Blue briefly carried "unassigned" on two screens and "field close" on a third — two meanings on one page, neither of them in the documented set. "Unassigned" is "not started", which is grey.

Keep `--blue` for genuinely non-status uses (links, informational callouts) or delete it. A fifth status would need a stated meaning, a tint, a dark value and a dot shape, and the four-colour set has not yet failed to express anything. `--faint` was failing AA at every size it was used (3.13:1 on white, 2.77:1 on `--surface-3`) while carrying most of the metadata layer; three of the four status hues failed on their own 6–7% tint at badge sizes; `--accent-strong` failed as link text. The corrected `--faint` still sits a clear 1.5× below `--muted`, so the three-tier hierarchy survives — the legitimate way to make a third tier quieter is size and weight, not contrast, since AA has no exemption for "deliberately faint".

**Focus is not `--focus`.** The ring is `outline: 2px solid var(--accent-strong); outline-offset: 2px`, applied once globally to `:focus-visible`. The `--focus` token is a 22% amber wash that computes to **1.17:1** — fine as a decorative inner glow behind a real ring, never as the indicator itself. The mockups use it as the indicator in two places and omit focus entirely everywhere else; both are defects, not the design.

Notes that matter when converting:

- **Status hues lighten in dark mode and the ink/tint relationship inverts in weight but not in form.** The tint is always `color-mix(in srgb, var(--x) 6-7%, transparent)`, derived from the hue, so a fifth status needs one token, not three.
- **`color-scheme`** on each block is what makes native scrollbars and form controls follow the theme. Easy to omit and immediately visible when missing.
- **`--topbar` is deliberately translucent** and pairs with `backdrop-filter: blur(16px)` on the sticky bar. It is the only place that effect is used.
- **Four surfaces and two line weights do the depth work.** This is why `--shadow` is optional (see `docs/mockups/README.md`) rather than structural.
- **Dark mode is `data-theme` on `<html>`**, persisted to `localStorage` as `pt-theme`, defaulting to `prefers-color-scheme`. The existing `.dark` class from the preset needs reconciling with this — pick the attribute, since the mockups and the toggle logic assume it.

### Not changed

The Phosphor and Mira choices above stand — both were made for this kind of application and the standard reinforces them. Phosphor's weight axis is directly what lets status avoid depending on hue (`frontend-standards.md` §2).
