# Visual reference — the template

Settled 2026-10-22. These artboards are the agreed template for the frontend: every React component is built to match them.

| File | Screen |
|---|---|
| `DashboardV2.dc.html` | Dashboard — three bands, 1360×1240 |
| `ProjectDetailV2.dc.html` | Project detail, 1360×1060 |
| `MobileQueueV2.dc.html` | Project pool, mobile, 390×844 |
| `canvas.json` | Canvas layout index |
| `v1-superseded/` | The first pass. Kept for comparison; copy nothing from it. |

They are **reference, not source**: `.dc.html` artboards for a canvas editor, hand-styled, with a `support.js` line that only resolves in that runtime. Nothing here is imported into `frontend/`.

Read with [`../frontend-standards.md`](../frontend-standards.md) (the rules, including who wins when the installed design skills disagree) and [`../design-tokens.md`](../design-tokens.md) (the authoritative token values). [`AUDIT.md`](AUDIT.md) records what was wrong with the first pass and what remains open — more useful than the superseded files themselves.

**Where these files and the docs disagree, the docs win.**

## What to build from

### Tokens

Both themes are declared in each file's `:root` / `:root[data-theme="dark"]`, identical across all three. Canonical values live in `design-tokens.md`; the structure is four surfaces, two line weights, three text tiers, brand plus focus, four status hues, and chrome.

Three rules the values alone don't tell you:

- **`--faint` only on `--surface` and `--surface-2`.** Elsewhere (sidebar, page ground) metadata uses `--muted`.
- **`--accent` is a fill, never text and never a lone indicator** (2.2:1). Focus rings and brand ink are `--accent-strong`.
- **Status is four colours.** Green, amber, red, neutral grey. `--blue` is in the palette but is not one of them.

### Metrics

| | |
|---|---|
| Control height | 34px desktop · 44px mobile minimum |
| Radius | 9px controls · 14px panels · 16px hero · 999px pills and chips |
| Sidebar | 248px sticky · Top bar 58px sticky |
| Content | max-width 1240px, `margin-inline: auto`, 24px padding (14px mobile) |
| Detail split | `minmax(0,1.7fr) / minmax(300px,0.82fr)`, 16px gap |
| Type scale | 10 caption · 10.5 metadata · 11 label · 12.5 body-sm · 14 body · 20 h1 · 21 metric |
| Tiles | `.tilegroup` + `.tile` + `.k`/`.v` — one pattern, `<a>` interactive, `<dl>` informational |

### Structure worth preserving

- **The dashboard's three bands** — Today (what must clear, each row stating *why* it is there and offering the action), Next two days (typed forward-looking commitments, day-grouped), then quiet context. The at-a-glance tile strip sits above all three and each tile filters the list.
- **Project detail leads with the current stage.** Pipeline is an `<ol>` with `aria-current="step"` and five distinct dot *shapes* (done, current, not started, blocked, not applicable) plus a legend.
- **Markets is a real `<table>`** with caption and column headers, in a labelled horizontal scroller.
- **Mobile is designed, not shrunk** — stacked rows keeping name / RDR+client / status / owner / delivery, 44px targets, one stretched link per card with the action button raised above it.

### Motion

Deliberately minimal: hover and press transitions at 140–160ms, `:active { scale(.96) }` on touch, progress widths transitioning at 300ms **on change only**. No entrance animations, no staggers, no infinite pulses, no theme-change transition. A global `prefers-reduced-motion` block is last in every file.

What the template does **not** yet draw, and the React build must add: loading skeletons, inline error states, and a permission-denied state. `frontend-standards.md` §8 requires them and `AUDIT.md` flags their absence as the largest remaining gap.

## Known limits of the template

Stated so they are not mistaken for decisions:

1. **Two responsive tiers, not five.** See `frontend-standards.md` §4 for the three the build owes, especially a working drawer at 768–1023.
2. **No skeleton, error or permission-denied states drawn.**
3. **Row actions are real buttons but inert**, revealed on `:hover, :focus-within`.
4. **The pipeline scroller overflows by ~4px at 1360.** Cosmetic; it is keyboard-reachable and labels are not truncated.
5. **Not verified at every width.** Rendered and inspected at 1360; the narrow tiers were checked in source only.
