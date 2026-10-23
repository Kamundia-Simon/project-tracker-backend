# Slice 0b — the frontend design system

Written 2026-10-23. The build plan for the frontend foundation: tokens, app shell, primitives.
Stage 1 has landed; Stages 2 and 3 have not started.

## Why this is one unit of work

`frontend-standards.md` §0 makes the design system the one deliberate exception to this repo's
vertical-slice rule: **tokens → app shell → primitives, built once before any page.** Built
after three pages exist it becomes a refactor of three pages, which is how an app ends up with
three button heights.

The timing was favourable: the frontend was effectively blank (landing page, `AuthPage`,
`BrandLoader`, `DevAuthToken` and `ui/button.tsx`), so there was nothing to retrofit.

`docs/mockups/AUDIT.md` items 1–16 ("Must fix in Slice 0b") and 17–26 ("resolve while building
the primitives") are the acceptance criteria for this work, not optional polish.

## Decisions settled 2026-10-23

1. **Token naming.** The brand family is `--accent` / `--accent-strong` / `--accent-ink` in
   code, matching `design-tokens.md`. `amber` no longer exists as a code name — it was a
   footgun, because the doc's `--amber` meant the status ochre `#8f5600` while the code's
   `--amber` meant the brand fill, so `text-amber` silently yielded a 1.57:1 fill colour as text.
2. **The brand amber.** Light `--accent: #ffd34e` (the logo artwork in
   `frontend/public/brand/3gem-mark.svg`), dark `--accent: #fbc804` (3gem.com). This resolves a
   contradiction in `design-tokens.md`, where the canonical block said `#fbc804` while the
   section heading above it said `#ffd34e`, and the code had one in each theme.
3. **The preset `--accent` was dropped.** shadcn's preset used `--accent` to mean "subtle hover
   surface". Since that name is now the brand, the preset's semantic names were instead pointed
   at the 3Gem palette (`--background: var(--canvas)`, `--primary: var(--accent)`, and so on).
   One palette rather than two parallel ones, and a registry component renders in 3Gem colours
   unedited. **Cost: a component copied from the shadcn registry that uses `bg-accent` for a
   hover state must be changed to `bg-surface-3`.**
4. **Headline amber is capped by contrast, not by preference.** `--accent-strong` `#8f6200` is
   already at sRGB's maximum chroma for its lightness, so there is no more saturated amber
   available at that darkness. Bright amber as text on the light ground is 1.32:1 and not
   usable. Bright amber needs a dark ground (12.55:1 on `--ink`) or it stays as fill.

## Stage 1 — the token layer — LANDED (commits 4a14625, accd9fc)

In `frontend/src/index.css`, `tailwind.config.js`, `src/lib/theme.ts`,
`src/components/ui/button.tsx`, and the `--accent*` rename across the landing components.

What it fixed:

- **Dark mode was broken, not merely unreconciled.** `.dark` (preset) and
  `:root[data-theme="dark"]` (3Gem) coexisted, but `body` used preset tokens that only switched
  under `.dark`, so setting `data-theme="dark"` swapped the 3Gem tokens while the page ground
  stayed white — and nothing toggled either. Now one mechanism: the attribute, with
  `darkMode: ["selector", '[data-theme="dark"]']` so the `dark:` variant follows the same
  selector instead of Tailwind v3's `media` default.
- **Inter was never applied.** The `.theme` class defining `--font-sans` was attached to no
  element, and there was no `fontFamily` extend, so `font-sans` resolved to the system stack.
  The webfont was bundled and unused.
- **Four absent tokens added:** `--rail`, `--topbar`, `--shadow`, and `--neutral` — the fourth
  status colour, which had no token at all, so `StatusBadge` would have improvised grey per
  instance ("unassigned", "on hold" and "not started" all land on it).
- **The radius scale** (9 control / 14 panel / 16 hero / 999 pill), with `rounded-md` and
  `rounded-sm` aliased onto the control radius so registry components land correctly for free.
- `color-scheme: light` on the light `:root`; a reduced-motion exemption for `BrandLoader` via
  `[data-motion="essential"]`, because a loading indicator whose only signal is motion becomes a
  static dot otherwise; `--font-mono` for RDRs, IDs and timestamps.
- `button.tsx`: heights to 34px desktop / 44px touch, the per-component focus ring removed in
  favour of the one global rule, a broken `color-mix` on bare OKLCH components fixed, and a
  loading state that reserves its width.

Verified: all 33 token values convert exactly to the hex palette in `design-tokens.md`;
`tsc -b` clean; production build succeeds.

### Closed in 323e05b and e0bfbfb

- `main.tsx` now calls `initTheme()` before `createRoot`.
- `buttonVariants` moved to `src/components/ui/button-variants.ts`.
- `AuthPage` wraps the Clerk widget in `ClerkLoading` / `ClerkLoaded`, so the brand loader
  covers Clerk's boot as well as the lazy chunk.
- **The theme now defaults to light rather than the system preference.** `resolveTheme()` is
  `storedTheme() ?? "light"`. This is a deliberate change from `design-tokens.md` line 197,
  which specifies `prefers-color-scheme`: an internal tool kept open all day beside other work
  should not go dark purely because the laptop is dark. `design-tokens.md` owes an update.

### Stage 1 follow-ups still outstanding

- **`button.tsx:54` still re-exports `buttonVariants`**, so `react-refresh/only-export-components`
  still fires. Splitting the file only helps if `button.tsx` exports the component alone —
  consumers import the variants from `button-variants.ts` directly.
- **`theme.ts:7` — `systemTheme()` is now dead** after the default changed to light, which fails
  both `tsc` (TS6133) and eslint. Delete the function.
- Hero headline is an inline `text-[#a37800]` literal. It works (3.70:1, valid for 24px+ text
  only) but a raw hex in a component is what §11 bans — it needs a token, and one scoped so it
  can never be reused at body size.
- `@clerk/clerk-react` ^5 is installed and unused; everything imports `@clerk/react` ^6.
- `tw-animate-css` is a Tailwind v4 package in a v3 project — it causes the
  `Unknown at rule: @utility` build warning and none of its classes are used.
- `index.html` still has Cpi-Dashboard's favicon and the scaffold `<title>`.

## Stage 2 — the app shell — NOT STARTED

`frontend/src/components/layout/`: `AppShell`, `Sidebar`, `TopBar`, `MobileDrawer`,
`PageHeader`, `Breadcrumb`.

Navigation is already settled in `docs/mockups/DashboardV2.dc.html`:

- **Workflow** — Dashboard · Project pool · Scripting · QA · Live / fieldwork ·
  Data processing · All projects
- **You** — My work · Change requests
- Signed-in identity at the foot (name + role)

Metrics from `docs/mockups/README.md`: sidebar 248px sticky · top bar 58px sticky · content
`max-width: 1240px`, `margin-inline: auto`, 24px padding (14px mobile).

Requirements that are the point of doing this once:

- **A real drawer at 768–1023px.** The rail hides there and the template's menu trigger opens
  nothing — "the single worst defect in both review passes" (§4). The main thing the React build
  owes over the artboards.
- The **theme toggle** lives in the top bar. `applyTheme()` already exists in `lib/theme.ts`
  and nothing calls it yet.
- `aria-current` carries the active state, never a parallel `.active` class (AUDIT 6).
- Counts are `<span>` + visually-hidden text, not `<em class="count">` (AUDIT 11).
- Notification `aria-label` from the unread count, not a bare red dot (AUDIT 9).
- Safe-area insets; 44×44px minimum touch targets (AUDIT 7).
- Mobile nav must not hide status and actions the way the template does (AUDIT 8).
- Skeletons shaped like the panels they replace, sidebar still rendered (AUDIT 27).
- `<h1>` at 20px with a real subtitle; no time-based greeting, no eyebrow (AUDIT 28, §1).

**`frontend/src/lib/labels.ts`** — the single central label map, from the enums in
`backend/models.py` (`Stage` ×10, `MarketStatus` ×7, `ChangeRequestStatus` ×3, roles `admin`,
`pm`, `scripter`, `qa`, `dp`, `viewer`). §12 and §6 both require stage and role names render
through one map: the DB says `pm`, the interface says Project Manager. Status labels are capped
here, not per page (AUDIT 12).

## Stage 3 — the primitives — NOT STARTED

`input`, `select`, `badge`, `table`, `dialog`, `drawer`, `toast`, `skeleton`, plus `StatusBadge`,
`DataTable`, `FilterBar`, `EmptyState`, `ErrorState`, `DataTile`, `Avatar`, `SearchField`.

- **`StatusBadge`** — two sizes, one pattern, border and tint always; never a filled amber badge;
  `.risk` is this component at hero size, not a second implementation (AUDIT 17, 18).
- **`DataTile`** — one component with a density prop, replacing the template's three
  implementations. Interactive is an `<a>`, informational is `<dl>`/`<dt>`/`<dd>` — carried by
  the element, not a prop, since a `<button>` inside an `<a>` is invalid. `.v` states its own
  colour so it cannot inherit a status hue from a parent (AUDIT 21, 5).
- **`DataTable`** — one list framework for all seven queues. Real table semantics, ellipsis plus
  `min-width: 0` and `title` on every text cell, stacked rows on mobile preserving the
  name / RDR+client / status / owner / delivery hierarchy (AUDIT 12, §4).
- **`EmptyState` / `ErrorState` / permission-denied** — none exist in any artboard, and §8 calls
  these "not edge cases" here. Needed before the pages, since everything inherits them (AUDIT 13).
- **One primary button only** — filled accent with `--accent-ink`. The near-black mobile `.claim`
  is the rejected resolution from `design-tokens.md` §1 (AUDIT 19).
- Null-safe throughout: `survey_type`, `final_delivery_date` and most market dates are
  legitimately null, with one shared "Not set" treatment (AUDIT 14).
- Type scale settled at caption 10 · metadata 10.5 · label 11 · body-sm 12.5 · body 14 (AUDIT 22).

## Verification

```
cd frontend && npx tsc -b && npx eslint src/ && npm run build
```

Then in the browser: flip `data-theme` between `light` and `dark` on `<html>` and confirm the
page ground, panels, borders and `dark:` variants all move together.

Re-check contrast after any token edit, for the pairs actually used — `--neutral` on `--surface`
and `--rail`, `--accent-ink` on `--accent`, the `--accent-strong` focus ring on `--canvas`, and
`--ink-faint` only on `--surface` / `--surface-2`, where it passes (it fails on darker grounds,
which is why that rule exists).

Run the `ui-reviewer` agent after Stages 2 and 3, giving it `frontend-standards.md` and
`AUDIT.md` so it reviews against our standard. Never load an aesthetic preset.

Finally, walk §13's coherence checklist before calling any stage done.

## Docs owed

- `design-tokens.md` — record the `--accent*` naming, `--neutral`, the dropped preset `--accent`,
  the `rounded-md`/`sm` aliasing, fix the `#ffd34e` / `#fbc804` contradiction, and change line
  197's `prefers-color-scheme` default to light.
- `phase-1-plan.md` §Progress — stale. Says "eleven tables", "Four migrations", "32/32 endpoint
  checks". Actual: 14 tables, 6 migrations, 145 checks in `scripts/unittests.py`.
- `CLAUDE.md` "Repository layout" — update the frontend paragraph as the shell and primitives land.
