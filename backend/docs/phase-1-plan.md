# Phase 1 plan

## Build order — revised 2026-10-22: backend to Live, then frontend to Live

The original plan was strict vertical slices. It is now **two horizontal passes with a hard boundary at `LIVE`**:

- **Pass A — backend through to Live.** Every endpoint needed to drive a project from the pool to launched, verified end-to-end by `scripts/unittests.py`.
- **Pass B — frontend through to Live.** The design system (0b) and every page covering the same ground, built against endpoints that already work.

**Why the change, and what it costs.** The vertical-slice rule existed to stop us building endpoints nobody uses and discovering the shape was wrong only once a page tried to consume it. That risk is real and we are accepting it deliberately, with two mitigations: `unittests.py` exercises every endpoint including its rejection paths, so "it works" is a verified claim rather than a hope; and the stop line is a genuine seam rather than an arbitrary one.

**Why `LIVE` is the right seam.** Everything up to launch is internal workflow this app fully owns — stages, roles, gates, checklists. The moment a project is live, progress comes from the CPI Dashboard integration (`architecture.md` §7, ADR 0004), which is a different kind of work: a polling job, a second system's availability, snapshot storage. Stopping at `LIVE` keeps Pass A to one coherent problem.

**In scope for Pass A** (stages `PM_ASSIGNMENT → SCRIPTING → QA → CLIENT_REVIEW → QUOTAS → LIVE`, plus `ON_HOLD`):

1. **`POST /api/projects/{id}/assignments`** and its close-out — the prerequisite for everything else. Without it a PM cannot put a scripter on a project, so no "only the assigned scripter may do this" rule is testable. Sets `unassigned_at` rather than deleting (ADR 0003).
2. **`GET /api/projects`** with filter, sort, search and pagination — every queue page in Pass B reads it, and the stage queues need it to exist.
3. **Checklist persistence** — `PATCH` of the scripting / QA / quota JSON state. Columns exist, nothing writes them.
4. **The transition endpoints**, named per action, sharing one `_transition()` helper: `send-to-qa`, `send-to-client`, `client-approve`, `client-request-changes` (writes a `revisions` row and routes back to the original scripter), `launch`, `confirm-soft-launch`, and `hold` / `resume`.
5. **`GET /api/projects/{id}/transitions`** — the timeline the detail page reads.
6. **Market endpoints up to launch** — create markets, and `PATCH /api/projects/{id}/markets` for the bulk-gesture status update (ADR 0009). Included because a multi-country project cannot reach Live without them, which is the case the markets work exists for.

**Explicitly out of Pass A:** fieldwork snapshots and the CPI polling job, data processing, final data QA, delivery and `merged_delivery_required`, change requests, notifications, comments, the audit-log viewer.

**Two prerequisites worth doing first**, both small:

- **`sub_status` is an unconstrained `String(32)`.** Pass A writes at least `AwaitingClient`, `SoftLaunch` and `FullLaunch` into it. A typo creates a ghost state that no query will ever match and no error will ever report. It belongs in `constants.py` as a validated vocabulary, the same treatment `survey_type` got — schema unchanged, validation at the boundary.
- **Named endpoints over a generic `POST /transition`.** The gates differ materially: `send-to-scripting` requires a survey type, `client-request-changes` writes a `revisions` row, `launch` checks quotas, and each has its own role rule. A generic endpoint collapses into a `match` over stage pairs holding exactly the same logic, one level deeper and harder to read, and loses the self-documenting URL in `/docs`.

The original slice list below still describes *what* each stage needs; it is the ordering that changed.

## Original build order — vertical slices (superseded as ordering, still accurate as scope)

A thin foundation layer first (built once), then one full-stack feature slice at a time — migration → SQLAlchemy model → Pydantic schema → endpoint → verify in FastAPI's `/docs` → matching React page → wire with TanStack Query → verify in the browser. Each slice should be usable end-to-end before starting the next.

## Progress (last updated 2026-09-14)

**Slice 0 — complete on the backend.** All eleven tables migrated onto a local Docker MariaDB (host port `33306`; see the project memory for the Windows reserved-port gotcha). Six roles seeded. `database.py`, `models.py`, `schemas.py`, `constants.py`, `auth.py`, `dependencies.py`, `rate_limit.py`, `cache.py`, `main.py` all working. A dev auth bypass (`ENVIRONMENT=development` + `DEV_AUTH_EMAIL`) exists because Clerk session tokens expire in ~60s — see ADR 0003.

The company MariaDB schema **`dbtracker` now exists** — the original blocker is gone. Development continues against local Docker by choice (wipe and re-migrate freely, works offline); moving over is a `DB_URL` change plus `alembic upgrade head`, which replays all three migrations including the seeded roles. Test data does not travel with it, so roles must be re-granted on the new schema.

*Frontend foundation is partial*: providers wired, theme applied, but `App.tsx` is still a header shell — no sidebar, router pages, or layout.

**Frontend foundation expanded 2026-10-15.** `docs/frontend-standards.md` sets the design language, and its §0 inserts a step before Slice 1's pages: tokens → app shell → primitives, built once. This is the second exception to vertical slicing (the first being the backend foundation) and for the same reason — a design system is only valuable before its dependents exist. The timing is favourable: the frontend is effectively blank, so there is nothing to retrofit. It also obliges four changes to the installed theme preset, recorded in `design-tokens.md` — most importantly that **amber is reserved for the warning status**, because the brand primary is also amber and a status colour that also means "button" stops being a status colour.

**Slice 1 — backend complete and verified (32/32 endpoint checks), frontend not started.** Four migrations applied (initial schema, `user_roles`, `survey_type`, `project_markets`/`change_requests`). Endpoints built across `routes/projects.py`, `routes/clients.py`, `routes/reference.py`, `routes/roles.py` and `routes/users.py` — the full list is in `architecture.md` §15. `backend/scripts/unittests.py` passes 32/32 against a running server, covering the rejection paths as well as the happy ones.

Closed since the last update: the clients dropdown endpoint, client details on project responses (nested object via a joined relationship, not a flat `client_name`), and the survey-type vocabulary — nullable on the project, validated at the schema boundary against `constants.SURVEY_TYPES`, and served to the frontend from `/api/reference/survey-types` so the two copies cannot drift.

All four gaps that blocked the pages are now closed: roles on `/api/me`, owners on the project detail response, user and role management endpoints (plus `scripts/grant_role.py` as the bootstrap path), and "Send to Scripting" — the first write to `stage_transitions` and the enforcement point for *logged without a survey type is fine, advancing without one is not*.

**Slice 1's backend is done. The remaining Slice 1 work is entirely frontend.**

Known gaps that are not blockers, carried forward:

1. **No general assignment endpoint** — self-assignment is the only path, so a PM cannot yet put a scripter or QA on a project. Needed by Slice 2. `project_assignments` already permits several people per role (no unique constraint on `project_id, role_id`); only `self_assign` enforces exclusivity, and only for `pm`.
2. **`GET /api/projects` (list-all with filters, sort, search and pagination)** — needed by the dashboard in Slice 8, but `frontend-standards.md` §14 gives it a second claimant: every queue page (scripting, QA, live, DP, my work, all projects) is one list framework over this endpoint, so it may need to arrive earlier than Slice 8. Sorting and filtering belong server-side; pagination rather than virtualisation, given ~20–25 users. Sidebar badge counts want a single counts call, not one request per queue.
3. **Rate limiting is a hard dependency of the whole app.** A Redis outage 500s every endpoint, because `SlowAPIMiddleware` reaches for `request.state.view_rate_limit` which `swallow_errors=True` never sets. Options at hardening time: drop the global middleware for per-endpoint `@limiter.limit(...)` decorators (preferred — the layer that protects the app shouldn't be able to break it), or treat Redis as genuinely required and monitor it. `cache.py` has the same shape of problem and should catch `redis.RedisError` per call.
4. **Networkless JWT verification with fallback** — still deferred to deployment, as is the `dbtracker` switch.

## Added after planning — multi-country and post-delivery work (agreed 2026-10-15)

Two requirements surfaced that the original schema could not express. **Both tables are migrated and live as of 2026-10-15** (revision `1ea73df725b2`), with no endpoints, schemas or tests yet — deliberately: **schema now, endpoints inside the slices that need them** — the same reasoning as putting rate limiting in the foundation, since migrating `stage_transitions` and `project_assignments` once they hold real history is the expensive version.

- **`project_markets`** (see `architecture.md` §16, ADR 0009) — per-market status, due dates and delivery for multi-country surveys. Tracking only: no per-market checklists, gates, notifications or assignments. Market endpoints land in Slice 3 (QA cycle), Slice 6 (launch) and Slice 7 (delivery). The per-market `due_date` is what fixes false lateness.
- **`change_requests`** (§17, ADR 0010) — post-delivery crossbreaks and retabulations, with the project staying `DELIVERED`. The change itself is free text (`title` + `description`), not an enum: the categories would have been guessed, and narrowing to picks later off a year of real titles is the cheap direction. Fully additive and coupled to nothing, so its endpoints and UI can slot in anywhere late in Phase 1.
- `projects.merged_delivery_required` was added with a `server_default` of true, so all eleven existing projects backfilled correctly. Worth remembering generally: a SQLAlchemy `default=` is Python-side and invisible to `add_column`, so a `NOT NULL` column added without `server_default` either errors in strict mode or silently backfills zero.

---

**0. Foundation** (one-off plumbing, not a feature slice itself)
- Backend/frontend scaffolding, Clerk wired on both ends
- DB connection + Alembic set up
- Base FastAPI app (CORS, exception handling, `Depends(get_current_user)`)
- Base React app shell: router, layout, sidebar
- `users`, `roles`, `project_assignments` tables + seeded roles
- Auth dependency + the permission policy module skeleton (see `architecture.md` §9)
- Redis wired up (local dev + Railway + Docker), `slowapi` rate limiting on the base app, a small `cache.py` helper for TTL-based caching (see `architecture.md` §13 / `decisions/0007-rate-limiting-and-caching.md`) — deliberately in the foundation layer so every slice after this one inherits it instead of adding it ad hoc

**0b. Frontend design system** (one-off, like Slice 0 — see `frontend-standards.md` §0). Visual target agreed 2026-10-16 and recorded in `docs/mockups/`; canonical token values in `design-tokens.md`.
- Tokens: the light/dark set converted to OKLCH in `src/index.css` — four surfaces, two line weights, brand + focus, four status hues with `color-mix` tints; plus typography, spacing, radius (9/14/16/pill), motion durations, breakpoints
- Dark mode: `data-theme` on `<html>`, persisted as `pt-theme`, defaulting to `prefers-color-scheme` — reconcile with the preset's existing `.dark` class, keeping the attribute
- App shell: 248px rail, 58px sticky top bar, mobile drawer + bottom bar, page header, breadcrumb
- Primitives: button (incl. the `aria-busy` loading state), icon button, input, select, status badge, filter chip, panel, data-table row, dialog, drawer/sheet, toast, skeleton (shimmer), avatar, empty state
- Motion as shared keyframes — `page-in`, `panel-in`, `card-in`, `grow`, `shimmer`, `soft-pulse`, `spin` — with a global `prefers-reduced-motion` block
- Central label maps for stage and role names, sourced from the enums in `models.py`, replacing the mockups' invented terminology — with status labels length-capped here rather than per page
- Build to the template in `docs/mockups/` (settled 2026-10-22). Its README lists five known limits the React build must close — chiefly a real drawer at 768–1023px and the skeleton / error / permission-denied states that are not drawn anywhere
- Tiles are one component: `.tilegroup` + `.tile`, with the interactive variant an `<a>` and the informational one a `<dl>`; they need different markup, not one component with an `onClick` (`frontend-standards.md` §2)
- Run `ui-reviewer` on the result, pointed at `frontend-standards.md` — and **render it**, since two of the defects in the last pass were invisible in source
- **Work `docs/mockups/AUDIT.md` as the checklist**: the global focus rule, the corrected token values, real table semantics for markets, operable checklist inputs, `aria-current` over `.active`, 44px touch targets, ellipsis on every text cell, and one designed empty/error state **before** the primitives, since everything inherits them

**1. PM Assignment** — `projects` table (core fields), project pool page, self-assign, project creation form, project detail page skeleton. This is the natural first slice since nearly everything downstream depends on a project existing. Built from the 0b components, not alongside them.

**2. Scripting** — scripting queue, self-assign, checklist reminder UI with persisted tick-state, "Send to QA" gated action, `stage_transitions` wired for the first time.

**3. QA** — QA queue, checklist, "Send to Client" action, `AwaitingClient` sub-status.

**4. Client Review sub-workflow** — approve / request-changes actions, `revisions` table, rework routing back to the original scripter.

**5. Quotas** — quota checklist reminder (reuses the Scripter checklist's quota section — no separate document exists), "Launch" action.

**6. Live / Fieldwork** — polling job calling the CPI Dashboard progress endpoint (built by the user separately), `fieldwork_snapshots`, soft-launch due/overdue flag, PM confirm actions, health computation.

**7. Data Processing** — DP work marker, Final Data QA checklist (QA role) → Ready for Delivery, PM "Confirm Delivered" action.

**8. Dashboard + My work** — the two pages the product is judged on; see `frontend-standards.md` §5, which specifies them in detail.
- Dashboard in three bands: **today** (what must clear before end of day), **tomorrow** (what lands in the next 48h — field closes, market due dates, merged deliveries, review windows ending; the band that makes this a planning tool rather than a worklist), and **helpful context** (stage distribution, workload per person, the four metrics).
- My work: one person's assignments across every stage at once, role-shaped, answering what's mine / waiting on me / waiting on someone else / due today and tomorrow.
- Needs `GET /api/projects` with filters, a merged upcoming-dates endpoint, `GET /api/me/work`, and the "waiting on me" derivation — all listed in `frontend-standards.md` §14.
- Open question carried: whether the dashboard is role-scoped or team-wide (§5).

**9. Notifications, comments, audit trail viewer** — polish pass across everything built so far.

**10. RBAC hardening** — final delivery-date lock rule, Head PM override flag, a pass over every mutating endpoint to confirm server-side enforcement (not just UI gating).

## Deferred to Phase 2 / 3

- Email notifications (in-app only for Phase 1 — email needs deliverability work that isn't worth doing twice)
- Escalations
- Advanced analytics: stage-time averages, client-turnaround charts, revision-cycle trend charts (the underlying data is captured from day one via `stage_transitions`/`revisions`, so this is a pure UI addition later, not a schema change)
- Editable/versioned checklist templates via an admin UI (Phase 1 checklists are hardcoded — see `decisions/0002-checklist-as-reminder.md`)
- DB-driven, admin-editable permission matrix (Phase 1 permissions are a small code module — see `architecture.md` §9)
- Deputy Head PM UI (the `is_head_pm_override` flag already supports it structurally; just no admin screen to toggle it yet)

## Open assumptions to confirm with the team before/during build

1. **Data Processing role boundary.** Working assumption: a DP role does the actual processing work; QA (not a separate role) performs the Final Data QA checklist sign-off before Ready for Delivery, matching the checklist's own "QA Analyst" field. Confirm this matches how the team actually splits the work.
2. **Soft-launch grace window** before a due flag becomes overdue — defaulting to 24 hours, easy to tune once live.
3. ~~**Panel modeling**~~ — resolved 2026-08-26: no `panels` table. Panel choice is a PM judgment call, not a fixed vocabulary, and panel/supplier identity already belongs to `Cpi-Dashboard`. `projects.panel_criteria` (free text) is the only trace of it.
4. **Dashboard scope** (raised 2026-10-21): role-scoped (admin/Head PM see everything, others see their own work plus their department's queue) or one team-wide dashboard for everyone? Written as role-scoped in `frontend-standards.md` §5 because a scripter shouldn't scroll past twenty PM rows to find four of their own, but it changes the endpoint shape, so confirm before Slice 8.
5. Delivery date lock: only `is_head_pm_override = true` users can edit a locked date. Confirmed only one person (Rose) needs it today; flag design leaves room for a deputy later without a migration.
