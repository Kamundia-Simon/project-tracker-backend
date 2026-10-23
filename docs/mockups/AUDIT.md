# Mockup audit — 2026-10-21

> **Status, 2026-10-22: largely closed.** The v2 artboards in this folder were built to fix these findings; a second review verified 24 of the 35 as genuinely resolved and the corrected tokens as actually in use. The findings below remain as the record of *why* the template looks the way it does — read them before changing it back. What is still open is listed in `README.md` under "Known limits", and the fixes that became rules now live in `frontend-standards.md` (tiles, focus, shadow, hover, motion, uppercase, responsive tiers) and `design-tokens.md` (values, the `--faint` ground rule, `--accent` as fill-only, blue excluded from status).
>
> The second pass also found eight defects **introduced by the fixes** — a focus rule that deformed corners, `color` inheritance that drained status hues from values and pills, a `<button>` inside an `<a>`, an invalid `<div>` between `<dt>` and `<dd>`, and a navigation range left with no navigation. All are fixed. The lesson worth carrying: **every one was a side effect of fixing something else, and two of them only showed up in a render.** Re-review after a fix pass, and look at the result.

An accessibility, motion and craft review of the three refined artboards, run with the `claude-code-frontend-skills` pack's `ui-reviewer`. Contrast ratios computed from the declared hex tokens, status tints resolved as `color-mix(in srgb, <hue> 6–7%, transparent)` over `--surface`.

**The mockups were not changed.** They remain the agreed visual target. This file records what must *not* be replicated when the design system is built, so Slice 0b builds the intent rather than the artefacts. Where this file and a mockup disagree, this file wins; where this file and `design-tokens.md` disagree, the token table wins.

**Not verified visually.** The review was source-based — no renders. Findings that depend on rendered appearance (the 720px stacked row, the pipeline scroller at narrow widths, the perceived weight of twelve panel shadows) should be confirmed against captures before acting.

## Fixed at token level — already corrected in `design-tokens.md`

| | Was | Now |
|---|---|---|
| `--faint` light — failed AA at every size used, carrying most of the metadata layer | `#92928b` 3.13:1 | `#76766f` ≈4.6:1 — **corrected again 2026-10-22 to `#70706a`**, since 4.6:1 held only against white |
| `--faint` dark — failed on raised surfaces | `#7d7d74` 3.66:1 | `#8b8b82` |
| `--green` light — badge text failed on its own tint | `#21875b` 4.12:1 | `#1b724d` |
| `--amber` light — same | `#a96500` 4.22:1 | `#8f5600` |
| `--blue` light — same, by 0.01 | `#3972b8` 4.49:1 | `#305f99` |
| `--accent-strong` light — failed as link and eyebrow text | `#a87400` 4.07:1 | `#8f6200` ≈5.2:1 |

Red passed at 4.64:1. Dark mode status passed throughout (4.99–7.28:1).

## Must fix in Slice 0b — accessibility

1. **Focus.** `--focus` computes to **1.17:1** (dark 1.45:1) and is used as the indicator in two places; every other focusable element — nav links, rows, icon buttons, buttons, tabs, chips, the claim button, bottom nav — has **no `:focus-visible` rule at all**. One global rule, per `frontend-standards.md` §2. `.search:focus-within` also signals focus with `border-color: var(--accent)` at 2.21:1.
2. **Markets table has no column identity.** Two bare mono dates per row, no header, differentiated only by `color: var(--green)` / `var(--red)` — colour alone, violating §2's absolute rule. Build it as a real `<table>` with `<caption>` and `<th scope="col">` (Due · Delivered). The mobile `.meta` tiles already label their values and are the right model.
3. **Pipeline state is colour + weight only.** No `aria-current`, no visually-hidden state word, and `blocked` / `not applicable` — both required by §5 — have no treatment at all. Use an `<ol>` with `aria-current="step"`, an `.sr` state word per step, and dot *shapes* per state (Phosphor's weight axis was chosen for this). The `overflow: auto` scroller contains nothing focusable, so a keyboard user cannot scroll it: `tabindex="0"` plus an accessible name.
4. **Checklist is not operable.** `<span>` with a literal `✓`; no checkbox, no role, no keyboard access, no label association. Real inputs in a `<fieldset>`/`<legend>`; expose the existing "3 / 5" text as the accessible value and mark the bar `aria-hidden`.
5. **Fifteen-plus orphan `<label>` elements** with no form control (`.stat label`, `.telemetry label`, `.meta label`, `.flow-row label`). Invalid, and some AT will bind them to the next control. Use `<dl>`/`<dt>`/`<dd>` — the `.kv` list already does this correctly.
6. **`aria-current` is the state, not a class.** The dashboard uses `aria-current="page"`; the detail page uses `class="nav active"` with no ARIA, so its active destination is styled but unannounced. Tabs likewise. CSS hooks off `[aria-current]`; never a parallel `.active`.
7. **Touch targets below 44px:** chips 32px (the whole filter row), claim button 38px (the card's primary action), icon buttons 42px, and an inline `height:28px` override on "Update selected". 
8. **Mobile hides data and capability rather than redesigning for it** — `.att .status, .att .stage { display: none }` drops the most-scanned thing in the app; `.actions .btn:not(.primary) { display: none }` removes *Add market* and *Confirm delivered* entirely; `.primary span { display: none }` leaves an icon-only link with **no accessible name**. §4 wants the row stacked and §5 wants secondary actions in a sheet. **This is more serious than the "one breakpoint" note in `README.md`** — a missing tablet layout is incomplete coverage; deleting status and actions is a different category.
9. **Unread indicator is a 6px red dot** with no text and no label; the button announces only "Notifications". Drive `aria-label` from the count.
10. **Decorative glyphs exposed to AT** — `›` reads as "single right-pointing angle quotation mark"; also `✓`, the `—` placeholders, `↑ 4%`. `aria-hidden` on the glyph, and real text for genuinely empty values ("Unassigned", "Not delivered").
11. **`<em class="count">` cancelled with `font-style: normal`** — wrong element, and it announces "Project pool 11". Use `<span>` plus `.sr` text. `.kbd` should be `<kbd>`.

## Must fix in Slice 0b — breaks on real data

12. **No `text-overflow` on the attention row's status, stage or owner columns.** "German market late" nearly fills its 142px; a realistic "Awaiting client sign-off on quotas" wraps and grows the row, breaking the scan rhythm of the one panel the product is judged on. Ellipsis plus `min-width: 0` on every text cell, `title` for the full value, and cap status labels centrally in the label map rather than per page.
13. **No empty, error or permission-denied state exists in any of the three files**, though §8 calls these "not edge cases" here. All four list patterns render populated. One designed empty state and one inline error state are needed *before* the primitives, since everything inherits them.
14. **`.kv` key column is `auto`** and will be crushed by a real label like "Expected field end date" in a 300px sidebar — `minmax(90px, 38%)`. Every `dd` is also populated, though `survey_type`, `final_delivery_date` and most market dates are legitimately null. The mobile card's `NOT SET` is the right idea; make it the one shared treatment rather than an inline style.
15. **Mobile card stagger is hardcoded to `nth-child(2/3/4)`** while the pool header says 11 projects, so cards 5–11 animate with zero delay and land as one block — reads as a rendering bug.
16. **Bottom-nav active bar positioned with `margin-top: 43px`** against an unpositioned parent. Any change to nav height moves the amber bar off its item.

## Consistency to resolve while building the primitives

17. **Status badge has three sizes and the mobile variant drops the border and tint** (10.5px / 9.5px / 9.5px bare) — three StatusBadge variants to reconcile, and the bare one has the worst contrast since it has no tint. Two sizes, one pattern, border and tint always.
18. **`.risk` is a second status implementation** — `border: color-mix(--red 42%, --line)` where every other status is `1px solid currentColor`. It *is* `StatusBadge` at hero size.
19. **Two different primary buttons** — desktop filled amber, mobile `.claim` near-black. The near-black one is the *rejected* first resolution from `design-tokens.md` §1 sitting beside the accepted one.
20. **`.card:before` paints a filled amber status rail** — small, but it is filled amber carrying a status, and the rule is absolute. Make it `currentColor` of the row's status hue so it reads as a status rail rather than as amber.
21. **Three implementations of "small labelled value tile"** — `.hero-stats`, `.telemetry`, `.meta`. One `DataTile` with a density prop. This is precisely the "three pages, three versions" failure the 0b-before-pages build order exists to prevent, already present in the reference.
22. **The type scale is not a scale** — metadata appears at 8.5 / 9 / 9.5 / 10 / 10.5 / 11 / 11.5 / 12 / 12.5 / 13 / 13.5px, with `.telemetry label` at 8.5px, below the README's own stated floor. Settle on: `caption 10 · metadata 10.5 · label 11 · body-sm 12.5 · body 14` and retire the rest.
23. **Radius drifts off the four documented values** — metrics at 12px, mobile controls at 10px, the bottom nav at 18px, small radii at 5/7/9px. 9 / 14 / 16 / 999 only.
24. **Reduced-motion blocks differ between files** (one includes `scroll-behavior`, two don't). One block, identical, last.
25. **Layout-bearing values inline** — `style="color: var(--amber)"` on five values is the worst of them, since a value's status colour is exactly what belongs centralised. Also a structural flex column written inline, `height:28px`, and the `margin-top:43px` magic number.
26. **The dashboard's primary action is an `<a href>` that takes `aria-busy` and a spinner.** A link that mutates should be a `<button>`; a link that navigates should not have a loading state.

## Craft — within the chosen aesthetic

27. **The boot loader is a full-screen blocking overlay** held on a fixed 520ms timer, showing a generic centred card resembling none of the three layouts. §7 asks for skeletons; a shimmering full-screen gate is a blocking spinner in a skeleton costume, and the timer delays a cached page that was ready instantly. Skeletons shaped like the panels they replace, driven by query state, sidebar still rendered. The `aria-label` on a plain `<div>` also needs `role="status"`.
28. **"Good evening, Rose." plus the `OPERATIONS OVERVIEW` eyebrow** own the most valuable pixels and say nothing. A time-based greeting is a consumer convention; on a tool opened forty times a day it is dead space above the fold, and eyebrow-over-heading-over-grey-sentence is the most recognisable generated-dashboard header there is. The sentence beneath it — "24 active projects · 5 require intervention before tomorrow" — is the only part working. `<h1>Dashboard</h1>` at 20px, that sentence as the subtitle, and the reclaimed space to the Today band. (`README.md` fixes the *word* "Command center"; this pattern survives that fix and shouldn't.)
29. **Zero-padded numerals** — `05`, `02`, `04`, `05 signals`, `07H 12M`. Padding a count is faux-telemetry styling; `05` scans as an identifier three columns from `RDR-2291`, and it breaks at three digits. Mono plus `tabular-nums` already gives the alignment padding pretends to provide.
30. **The dashboard is a statistics page in its top third**, which §5 forbids. Four metric cards with trend chips own the first band; the Today / Tomorrow / Helpful-context structure §5 calls "a requirement, not a nice-to-have" is absent — one "Priority queue" and four quiet right-rail rows stand in for the entire Tomorrow band, and the metric set is positioned as hero rather than quiet support. **This is the largest gap between the mockup and the documented product intent**, and because the mockup is the agreed visual target it will otherwise get built as drawn. The attention row is already 80% of the Today band; it needs the "why it's here" column it currently spends on status.
31. **A surveillance-console register** — "Workflow signal", `AUTO-STAGE ENABLED`, "Fieldwork telemetry", `SYNC 11M AGO`. `README.md` flags the individual strings; the register is the deeper problem, since it is what makes a first impression read as "AI-generated ops dashboard" rather than "3Gem's tracker". Five uppercase-mono pseudo-badges also break §2's sentence-case rule.
32. **Every panel head carries a subtitle whether or not there is anything to say** — "Human and system events in chronological order" under "Activity stream" is template filler. Keep a subtitle only where it states a parameter the user cannot infer (a non-obvious sort order); drop the rest and let the panels tighten, which serves the density goal.
33. **`.trend` mixes deltas and imperatives in one slot** — `+3 this week`, `↑ 4%`, `review`, `escalate`. The imperatives look like links while being inert text. One content type per slot.
34. **`.metric:hover` lifts a non-interactive element** — a hover affordance with no target behind it. Remove, or make the metric a link to the filtered list, which would also serve §5's "anything that doesn't inform a decision gets cut".
35. **The logo rotates 8° on hover.** §1's "decorative elements with no function", verbatim.

## Motion verdicts

Covered in `frontend-standards.md` §7 as revisions. In short: **cut** page-in, the panel stagger, `soft-pulse`, the theme transition, the row `translateX`, the button lift and glow, and the logo tilt. **Keep** shimmer skeletons (in place, not as an overlay), the button spinner (without the width change), `:active` press scale, and hover background/border swaps. **Rework** `grow` to animate on change at 300ms rather than on every mount, and the mobile list stagger to be first-load-only and bounded.

## Conflicts raised by the pack, and how they were settled

Three were settled by our own documents, with no real conflict: the pack's 300–400ms spring entrances exceed §7's own ceiling (§7 wins — those numbers are tuned for marketing surfaces, not a page opened forty times a day); the "genuinely faint third tier" argument against raising `--faint` loses to §9's AA target, and size and weight are the legitimate way to quieten a tier; and table-vs-anchor semantics split by case — a real table for markets, `<ul>`/`<li>` with an anchor per row and `.sr` column labels for the clickable attention rows, which honours "real table semantics" without forcing it where the row is a link.

Three were decided by the user on 2026-10-21: **no filled amber** (chip goes near-black — the rule stays absolute, since a borderline case that is merely defensible is not enough to open an exception); **shadow off panels, metrics and hero**, kept only for genuinely floating surfaces and the mobile card list; **hover is background and border only**, with `:active` press scale retained on touch.
