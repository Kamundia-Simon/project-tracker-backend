# Frontend standards

Agreed 2026-10-15, before any application page exists. This is the frontend counterpart to `architecture.md` — it governs *how* screens are built, while `architecture.md` governs what they contain.

The target is operational software that a PM uses all day: dependable, dense, calm, fast. The quality reference is Linear / GitHub / Stripe Dashboard — for hierarchy, density and interaction quality, not for visual imitation. It must read as one product designed once, not as a set of independently generated screens.

**The template is `docs/mockups/`** — `DashboardV2`, `ProjectDetailV2`, `MobileQueueV2`, settled 2026-10-22 after two review passes and a rendered verification. They are the reference every React component is built to match. The first-pass artboards are kept in `docs/mockups/v1-superseded/` for comparison only; nothing should be copied from them. `AUDIT.md` records what was wrong with them and why, which is more useful than the files themselves.

**Where a mockup and this document disagree, this document wins.** Where this document and `design-tokens.md` disagree on a value, the token table wins.

## 0a. The installed design skills, and who wins

A marketplace of frontend design skills is installed (`frontend-stack` router, `impeccable`, `taste:*`, `emil-design-eng:*`, `ui-ux-pro-max:*`, plus the `ui-reviewer` and `design-director` agents). They are useful and they are **advisory**. The order of authority, which matches the router's own precedence ladder:

1. **The user's explicit decision**, including ones recorded here.
2. **This project's system** — `frontend-standards.md`, `design-tokens.md`, `docs/mockups/`.
3. **Accessibility and correctness** — contrast, focus, keyboard, reduced motion. A pack finding here is almost always right and should simply be fixed.
4. **The packs' own taste.**

What they are good for, demonstrated twice on this project: **computed contrast ratios, semantics, state coverage and motion judgement.** Both audits found real defects that reading the source had missed, including six token values failing AA and a focus ring at 1.17:1. Run `ui-reviewer` after any significant UI work, and give it this document plus `AUDIT.md` so it reviews against our standard rather than its defaults.

What they must not do: **redirect the aesthetic.** `taste:soft-skill` (premium agency), `taste:minimalist-ui` (editorial) and `ui-ux-pro-max`'s style catalogue all have a look they will steer toward, and this project's look is decided. Do not load an aesthetic preset. Tell a reviewing agent the direction is settled, or it will spend the report recommending more whitespace.

Three pack positions we have **adopted**, because they were right: browser surfaces (`::selection`, caret, scrollbars) are themed rather than left as browser defaults; the eyebrow-above-a-heading pattern is banned outright; a coloured left border on a card stays at 1–2px and must carry meaning, never decoration.

Three we have **declined**, with reasons recorded so they are not re-litigated: 300–400ms spring entrances (tuned for marketing surfaces; this is a page opened forty times a day, so §7's ceiling stands); hover lift plus shadow bloom (invents a depth level our surface ladder does not have); and a genuinely faint third text tier (AA has no exemption for "deliberately quiet" — quieten with size and weight instead).

## 0. Build order — the design system comes first

The one deliberate exception to this repo's vertical-slice rule.

Slices are the right unit for features because a feature is only valuable end-to-end. A design system is the opposite: it is only valuable *before* the things that depend on it. Built after three pages exist, it becomes a refactor of three pages, and refactors that aren't urgent don't happen — so the three pages each keep their own spacing, their own button height and their own idea of what a status looks like. That is exactly the incoherence this document exists to prevent.

Order:

1. **Tokens** — colour, type, spacing, radius, motion, breakpoints. Central, semantic, no page-level overrides.
2. **App shell** — sidebar, top bar, mobile navigation, page header, breadcrumb.
3. **Primitives** — button, input, select, badge, table, dialog, drawer, toast, skeleton, empty state.
4. **Then slices resume.** Slice 1's pool page, create form and detail page are built *from* those components.

Steps 1–3 are the frontend's foundation layer, the same category as Redis and `get_current_user` on the backend. Everything after inherits them.

When a slice needs a pattern that doesn't exist, the first question is whether an existing component can be extended. A new primitive is a deliberate addition to the system, not a local convenience.

## 1. Anti-goals

These are the failure modes to design against, listed because they are what "AI-generated interface" actually means in practice:

Arbitrary gradients · everything wrapped in a rounded card · oversized headings · inconsistent spacing · random shadows · glassmorphism · decorative elements with no function · a different styling pattern per page · inconsistent button heights and radii · large dead space · excessive animation · non-semantic colour · dashboard widgets nobody acts on · emoji as icons · a desktop layout merely scaled down for mobile.

Polish comes from hierarchy, spacing, typography, interaction and consistency. Not from effects.

## 2. Tokens

Semantic names only — a component asks for `border`, never for a specific colour value. See `design-tokens.md` for the actual values and for the four resolutions this standard forced on the original preset.

Required semantic set: `background`, `surface`, `surface-elevated`, `sidebar`, `border`, `border-subtle`, `primary`, `primary-hover`, `text-primary`, `text-secondary`, `text-tertiary`, `success`, `warning`, `danger`, `info`, `focus-ring` — each defined in both light and dark.

**Status colour is a fixed vocabulary**, identical in every context it appears:

| Meaning | Colour |
|---|---|
| healthy, complete, approved | green |
| needs attention, at risk, pending, awaiting someone | amber |
| overdue, error, blocked | red |
| inactive, on hold, not started, not applicable | neutral grey |

**Never colour alone.** Every status carries a label, and where space is tight, an icon shape or weight. Phosphor's multiple weights were chosen partly for this (`design-tokens.md`): a pending checklist item and a done one differ in weight as well as hue. This is not only an accessibility rule — status is the single most scanned thing in this app, and it has to survive a greyscale print, a colourblind user and a bad monitor.

**Spacing scale:** 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48. Nothing in between, invented per component.

**Radius:** 9px controls · 14px panels · 16px hero · 999px status badges and filter chips. Controls visibly tighter than their containers is what reads as deliberate; one radius everywhere is what reads as generic. Pill shape is reserved for states and chips.

**Amber has one rule and it is absolute:** filled amber = action, amber ink on a 6–7% tint = status. Never a filled amber badge, never an outlined amber button. `design-tokens.md` §1 has why this is the whole basis of the brand surviving alongside the status vocabulary.

**Elevation:** four surface levels (`--bg` / `--surface` / `--surface-2` / `--surface-3`) and two line weights (`--line` / `--line-strong`) carry the depth. **Shadow is limited to things that float** — dropdowns, popovers, modals, drawers, floating mobile controls, and the mobile card list, where it separates a scroller from its ground. Decided 2026-10-21: `--shadow` comes **off** `.panel`, `.metric` and the hero, which the mockups apply it to. Twelve soft shadows on one 1360px screen is what makes a dense layout read as soft, and at `.06` alpha over `#f6f6f4` it mostly just blurs the border behind it.

**Focus:** one global rule — `:focus-visible { outline: 2px solid var(--accent-strong); outline-offset: 2px }` — on every interactive element, written once rather than per component. Never the `--focus` wash alone (1.17:1), and never only on the search field. This is the single easiest thing to leave out and the hardest to notice missing, since a mouse user never sees it.

**Tiles — one pattern, two behaviours** (unified 2026-10-22; see `docs/mockups/`). Every labelled-value tile in the app is the same component: a `.tile` with a `.k` label (11px, `--muted`, optional status dot) and a `.v` value (12.5px, or 21px with `--lg`), inside a `.tilegroup` that supplies the column count. Three variants of container, no variants of tile: default (bordered strip with dividers), `--flush` (seamless under a hero), `--gap` (separate boxes, used on mobile and for inset groups).

The one distinction that matters is **interactive vs informational, and it is carried by the element, not a prop**. An interactive tile is an `<a class="tile">` — it gets hover, `:active`, a pointer cursor and the global focus ring. An informational tile is a `<div>`/`<dt>`/`<dd>` inside a `<dl>` and gets none of those. Never give a static tile a hover affordance that leads nowhere, and never build the clickable variant out of `<dl>` markup: wrapping `<dt>`/`<dd>` in an anchor is invalid, so the two genuinely need different markup rather than one component with an `onClick`.

Two traps, both found by rendering rather than by reading the source:

- **`.tile .v` sets `color` explicitly.** Without it, a value inherits from any ancestor that sets `color` to carry status — the mobile card does — and every date and count silently renders in the status hue. The same inheritance trap bit the mobile status pill through `currentColor`. Any component that may sit inside a status-coloured container states its own colour.
- **A clickable card is one stretched link, not nested interactive elements.** `.namelink::after { position: absolute; inset: 0 }` makes the whole card the target while keeping a single anchor; a sibling button raised above it (`z-index`) stays separately clickable. A `<button>` inside an `<a>` is invalid and produces "the action also navigated" bugs.

**Hover:** background and border-weight (`--line` → `--line-strong`) only. Decided 2026-10-21: no `translateX` on rows — sliding a row sideways in a dense table makes its text jitter against unmoved neighbours and makes the pointer feel like it's shoving the UI; no `translateY` lift or coloured glow on buttons, because if a resting panel has no shadow then a hovered one gaining one invents a depth level the surface ladder doesn't have. `:active { transform: scale(.96) }` on touch stays — press feedback is the one transform clearly earned.

**Typography:** one disciplined scale with defined styles for page title, section title, panel title, body, secondary body, label, metadata, table header, caption, numeric metric. Few weights. Inter for interface text; a monospace face **only** for RDR numbers, IDs, timestamps and numeric data — see `design-tokens.md` §Mono, since this is a new decision the preset didn't cover.

Interface text is **sentence case**. Not title case, not inconsistently either.

**Two documented exceptions, and only these two** (settled 2026-10-22): table column headers and sidebar section labels may be uppercase at 10.5–11px with ≤0.09em tracking. Both are conventional in dense tools, both are structural rather than prose, and both are read as landmarks rather than sentences. Everything else — headings, buttons, badges, tile labels, panel titles — is sentence case. Note the trap this creates: uppercase micro-type plus wide tracking *is* the eyebrow pattern that §1 bans, so these two exceptions are the boundary, not a licence.

## 3. Shell and navigation

Desktop: persistent sidebar plus main workspace. The sidebar separates workflow navigation (queues, stages) from personal navigation (my work, settings), shows the active destination unambiguously, supports counts, carries the signed-in user's identity, and stays visually quiet. The top bar carries context and utilities — breadcrumb, search, notifications, theme, profile, page-level actions — and never duplicates the sidebar.

Mobile is **designed, not derived**. The sidebar collapses to a drawer holding the full navigation; a compact bottom bar may carry only the few most-used destinations. Every workflow section stays reachable. Primary actions should be reachable one-handed where practical. Respect safe-area insets. Minimum touch target ~44×44px.

## 4. Responsiveness

Part of the system, not a breakpoint bolted on at the end. Deliberate behaviour at 320–479 / 480–767 / 768–1023 / 1024–1439 / 1440+. Fluid layouts between those, not five unrelated designs.

**Where the template actually stands** (be honest about this when building from it): the artboards implement **two** of the five tiers — a desktop form and a ≤1023px form — plus a 1199px adjustment and a 767px one. That is a deliberate limit of a static artboard, not a target. Three things the React build owes:

- **768–1023 needs a real drawer.** The rail hides there; a menu trigger exists in the top bar but opens nothing. Hiding navigation with no replacement was the single worst defect in both review passes, and moving the breakpoint from 720 to 1024 *widened* that range before the trigger was added.
- **1024–1199 is tight, not broken.** The template drops the Due column and widens the reason column. Verify with real strings rather than trusting it.
- **1440+ needs more than a centred max-width.** `margin-inline: auto` is in place so content stops pinning left, but extra width should go to the Tomorrow band rather than to gutter. Reading content gets a max width; data-dense areas may use the full viewport. Controls never overflow out of reach.

**Tables are the hard case.** A project table must not become a horizontally scrolling desktop table on a phone. Per table, choose deliberately between a responsive table, contained horizontal scroll with the identifying column pinned, or stacked rows. Stacked project rows follow this hierarchy:

```
Project name
RDR · Client
Stage / status
Owner
Delivery date
Contextual action
```

Hierarchy survives the transformation; the layout changes, the priority order does not.

## 5. Information hierarchy

Priority order, applied on every screen: what needs attention → status → ownership → deadlines → current stage → blockers → progress → available actions → history. Secondary metadata stays visually secondary. A user should understand a screen's state by scanning it, without reading sentences.

### The dashboard and My work — the two pages the product is judged on

These two carry the operational value. Everything else in the app records state; these two are where someone decides what to do. Design them as a pair with a clear division of labour, and build neither as a statistics page.

**Dashboard — run today, prepare tomorrow.** Three bands, in this order:

1. **Today.** What must happen before the end of the day: overdue items, soft launches needing review, projects awaiting a client who has gone quiet, anything sitting unassigned, anything ready for delivery and waiting on a confirmation. Each row states *why* it is here and offers the action that clears it.
2. **Tomorrow.** The forward-looking band, and the part that makes this a planning tool rather than a worklist. What lands tomorrow and the day after: field closes, market due dates, merged deliveries, client review windows ending, soft launches due to be decided. The purpose is to surface the thing that will become a crisis overnight while there is still an evening to act in — a scripter who needs briefing now, a client who needs chasing before they leave, a translation that has to be commissioned today to make Thursday.
3. **Helpful context.** Where the work sits by stage, workload per person, and the small metric set (active / on track / at risk / overdue). Supporting information, visually quieter, no wall of charts. Anything here that doesn't inform a decision gets cut.

The "tomorrow" band is the distinguishing feature; treat it as a requirement, not a nice-to-have. A dashboard that only shows what is already late tells you about failures you can no longer prevent.

**My work — the personal operating surface.** The same data narrowed to one person, and the page most users will keep open all day. It answers, in order: what is mine right now, what is waiting on me specifically, what is waiting on someone else so I know not to chase it, what of mine is due today and tomorrow, and what I've just finished. It spans stages — a PM has projects in scripting, in fieldwork and in delivery simultaneously, and splitting those across five queue pages is what the page exists to fix.

It is role-shaped, because "mine" means different things: a PM sees projects they own, a scripter sees scripting assignments, QA sees review queues, DP sees processing and open change requests. One page, one layout, the rows filtered by the viewer's own assignments.

**Scope assumption to confirm:** the dashboard is written as **role-scoped** — `admin` and `is_head_pm_override` see everything, everyone else sees their own work plus their department's queue. My work is always personal. The alternative is one team-wide dashboard for all, which is simpler but makes a scripter scroll past twenty PM-owned rows to find their four. Worth confirming with the team, since it changes the endpoint shape.

**Queues are one family.** Project pool, scripting, QA, live, data processing, all projects and my work share a single list framework with sorting, filtering, search, hover and focus states, keyboard navigation, visible status, ownership, delivery date and row actions. Not seven list implementations.

**Project detail is the core workspace** and gets the most attention. Stable architecture: header (RDR, name, client, health, current stage, primary actions, the user's own role on it) → workflow pipeline → main content weighted toward the *current* stage → activity timeline. Sections do not all get equal visual weight; the current stage is why the user opened the page. The pipeline must distinguish complete, current, future, blocked and not-applicable, and degrade gracefully on narrow screens. Activity shows action, actor, timestamp and context, and visually distinguishes system activity from human activity.

On mobile, project detail leads with current status and actions, stacks secondary detail, collapses long history, and uses sheets for secondary actions. Smaller screen, same capability.

## 6. Permission UX

Authorization is enforced server-side and always will be (`architecture.md` §9); the UI's job is to make it *legible*, never to be the enforcement.

An action the current user cannot take is either hidden, when the action is irrelevant to them, or shown disabled with a stated reason, when knowing it exists is useful — "only this project's PM can send it to scripting" is information; a greyed button with no explanation is a puzzle. Do not fill screens with disabled controls.

Role names render consistently and in human form: the DB says `pm`, the interface says Project Manager. Map once, centrally. A user should be able to tell what they own, what they can edit, what is read-only, and who owns the next step.

## 7. Motion

Motion explains navigation, hierarchy, state change, causality and feedback. Motion that only demonstrates that animation exists is removed.

| Purpose | Duration |
|---|---|
| hover / press feedback | 100–150ms |
| small component transition | 150–220ms |
| drawer / popover | 200–300ms |
| larger layout transition | 250–350ms |

Ease-out, or a restrained spring where it genuinely helps. Animate `transform` and `opacity`; animating layout needs a reason. No large animation dependency — CSS transitions cover nearly all of this, and the few cases that need orchestration can be added deliberately.

Worth animating: the sidebar's active indicator; drawer and popover entry; status badge and pipeline advancing on a stage change, with a toast confirming; checklist tick and its progress; row hover; modal backdrop fade. Content areas load as skeletons, not blocking spinners.

**Revisions after the 2026-10-21 motion audit** (`docs/mockups/AUDIT.md`), because the mockups exceed this section's own limits:

- **Page and panel entrances: cut.** 380ms with a staggered 60/100/140ms cascade puts the last panel at ~520ms, on a page opened forty times a day. A stagger communicates sequence; these panels have none, so it is choreography for its own sake and the clearest "generated dashboard" tell in the set. At most a 150ms opacity fade, never on a container *and* its children.
- **Progress bars animate on change, not on mount.** A bar you have looked at twenty times today should render at its final value; it animates when the number actually moved. 300ms, and animate `width` or an inner unrounded fill — `scaleX` on a `border-radius: 999px` bar distorts the end caps throughout. The pipeline's completed segments must never all fill at once, which reads as a glitch.
- **No infinite animation unless something is genuinely live.** A pulsing dot means "this value is updating right now" and stops when the request settles. A dot pulsing forever beside static copy, in peripheral vision, all working day, is the one piece of motion here that will actively annoy.
- **No theme-change transition.** Transitioning only the root crossfades the page ground for 220ms while every panel, border and badge snaps instantly, which looks more broken than an instant swap. A `* { transition-duration: … !important }` escape hatch is a bug factory in a component codebase.
- **Loading buttons must not resize.** Swapping the label for a spinner changes the button's width mid-interaction and reflows the row; reserve the width, or keep the label with the spinner in a fixed leading slot. Toggle visibility rather than replacing children, so focus survives, and announce the outcome via `aria-live`.
- **List entrances, if kept, are first-load only** and capped — never on every filter change, or tapping five chips means five cascades. Stagger with a bounded `calc()`, never hardcoded `nth-child` delays, which silently stop working past the last index written.

`prefers-reduced-motion: reduce` is honoured, with full functionality retained — reduced motion means instant, never broken or hidden.

## 8. States

Every component accounts for: default, hover, focus, active, selected, disabled, loading, success, warning, error, empty.

Every screen accounts for the unhappy paths, which in this app are not edge cases: no projects, no notifications, no search results, API failure, partially loaded data, permission denied, connection lost, a 90-character client name, a four-digit count, and missing optional values — `survey_type`, `final_delivery_date` and most market dates are all legitimately null (`architecture.md` §8). A layout that only works when every field is populated will break on real data in week one.

Micro-interactions that earn their place: tooltips on ambiguous controls, visible keyboard focus, pressed states, inline validation, optimistic updates where safe, contextual loading, hover disclosure of row actions, confirmation after mutations, useful empty states, meaningful errors, contextual undo.

## 9. Accessibility

WCAG 2.2 AA as the target. Semantic HTML, full keyboard operation, visible focus, accessible dialogs, correct ARIA, real table semantics, sufficient contrast, status never by colour alone, sane heading order, touch-friendly targets, reduced-motion support, labels on icon-only buttons. Visual minimalism is not a reason to drop any of it.

## 10. Icons

Phosphor only (`design-tokens.md`). One library, no mixing. Icons aid recognition; they don't replace a clear text label. Icon-only buttons are for conventional meanings, and always carry a tooltip and an accessible label.

## 11. Code structure

Central tokens, typography, motion and breakpoints. Reusable primitives, then shared layout components, then feature components. Shared data-table, feedback and accessibility behaviour rather than per-page reimplementation. Business logic separate from presentation where practical. No page-level styling unless that page is genuinely unique.

Note the tension with this repo's "no premature abstraction" rule (`CLAUDE.md`): that rule is about *speculative* helpers for logic used once. A design token or a shared Button is the opposite — it is used everywhere immediately, and duplicating it is what costs. Three similar lines of logic are fine; three different button heights are not.

## 12. Preserve the product model

The redesign improves presentation and interaction. It does not invent workflow.

The stages, sub-statuses, role ownership, permissions, queues, deadlines, checklists, client review loop, fieldwork and data-processing steps are all defined in `architecture.md` and the ADRs, and they stay. In particular this is **not** a Kanban board: the lifecycle is a gated sequence with per-stage ownership, which a free-form board actively misrepresents.

Stage names in the interface come from the `Stage` enum in `models.py` via a single central label map — never retyped per page, and never paraphrased into a nicer-sounding word on one screen. Terminology is fixed: if the product says "data processing", every screen says that.

## 13. Coherence check

Before any screen is called done: same spacing system? existing components? typography from the scale? semantic colours? behaviour consistent with similar controls? mobile state deliberately designed? motion useful? keyboard operable? hierarchy immediately clear? does it look like the same product? Any "no" is a revision.

## 14. What this standard requires from the backend

Recorded here because the design implies API work that doesn't exist yet:

- **`GET /api/projects` with filter, sort, search and pagination.** Every queue and the "all projects" list need it; only `/pool` exists today. Already carried as a known gap in `phase-1-plan.md`, now with a second reason.
- **The dashboard's "tomorrow" band needs a date-window query across three sources** — `projects.final_delivery_date`, `project_markets.due_date` and `projects.expected_field_end_date` — merged into one ordered list with a type on each row. Three separate requests the frontend stitches together would be the wrong shape: the ordering is the whole point, and it can only be done correctly server-side. One endpoint, something like `GET /api/dashboard/upcoming?from=&to=`.
- **`GET /api/me/work`** for My work: the viewer's current assignments across every stage, with the same row shape the queues use. Derivable from `project_assignments` where `unassigned_at IS NULL`, so no schema change — but it is a genuinely different query from any queue endpoint, because it spans stages instead of filtering to one.
- **A "waiting on me" vs "waiting on someone else" distinction.** This is a derivation, not a column: it comes from the current stage plus who holds the role that stage belongs to. Where that logic lives needs deciding — most likely beside the permission policy module (`architecture.md` §9), since it answers the same kind of question, and definitely not duplicated in the frontend.
- **Server-side sorting and filtering, not client-side.** Shipping the whole table to the browser to sort it works until it doesn't, and it makes pagination meaningless.
- **Pagination, not virtualisation.** At ~20–25 users and a few hundred live projects, pagination is sufficient and far simpler. Virtualisation is the answer to a problem this app does not have.
- **Counts for sidebar badges**, ideally in one call rather than one per queue.
- **Saved filters would need a table.** Phase 2 unless it proves essential.
- **Notifications** already have a table and no endpoints (Slice 9).
