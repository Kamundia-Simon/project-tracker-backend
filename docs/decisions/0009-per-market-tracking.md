# 0009 — Multi-country surveys: per-market tracking, not per-market workflow

## Context

A multi-country survey does not move through the lifecycle as one thing. After scripting and the first link verification, only the English link is approved, and it can launch before any other market exists. The remaining markets are then translated, go through QA, go to the client for verification (mostly wording, so it returns faster), and launch later. Fieldwork and delivery overlap: English may be delivered while other markets are still live.

A `projects` row holds one `stage` column. The schema therefore cannot represent "English is LIVE while France is in QA" — there is nowhere to put the second state. Delivery has the same problem: `final_delivery_date` is singular, and `DELIVERED` is one stage for the whole project.

Delivery dates are the sharpest version of it. If English was due 16 October and Germany 20 October, evaluating the project against a single date reports a late project when both markets were on time.

Until now `survey_type` carried the only trace of multi-country work — a label, with no structure behind it.

## Decision

A `project_markets` child table, carrying a **status field rather than a stage machine**:

```
project_markets   id, project_id FK, country, language, is_primary BOOLEAN,
                  status ENUM, due_date DATETIME NULL, live_start_date DATETIME NULL,
                  delivered_at DATETIME NULL, created_at, updated_at
                  -- UNIQUE(project_id, country)
```

```
PENDING → TRANSLATION → QA → CLIENT_REVIEW → APPROVED → LIVE → DELIVERED
```

The primary market is created at `APPROVED`, having reached that through the project's own scripting, QA and client-review stages. There is no per-market `ON_HOLD`; the project-level stage covers it.

**Markets are tracking records, not workflow.** No per-market checklists, no per-market gates, no per-market notifications, no per-market assignments.

**Single-country projects have no market rows at all.** Zero rows means no market constraints, and anything consuming markets treats an empty list as "nothing to track". No backfill, no markets panel in the UI for the common case.

**Lateness is evaluated per market, never project-wide.** Each market's `due_date` is the date that market was promised; `delivered_at` is when it was actually sent. `projects.final_delivery_date` becomes the date of the **merged/final deliverable** — and remains the only date for single-country projects. A project is late if, and only if, a market missed its own `due_date` or the merged delivery missed `final_delivery_date`. Project health is the worst state among its parts, not a comparison against any single date.

**Per-market delivery is optional.** Sometimes each country is sent separately and then merged; sometimes only the merged file is sent; roughly 90% of the time a merged file exists. `projects.merged_delivery_required` (BOOLEAN, default true) records which shape applies, and `delivered_at` on a market records an interim send when one happened.

**Markets do not gate project delivery.** The existing QA → Ready for Delivery → PM Confirms Delivered flow is unchanged. The project page shows an advisory line ("2 markets still live") rather than disabling the button.

**Bulk gesture, individual records.** Markets are usually approved at the same time but cannot be basketed as one record. `PATCH /api/projects/{id}/markets` takes a list of market ids and one status, updating each row separately so each keeps its own dates and history.

## Why

*A child table rather than child projects.* Giving each market its own `projects` row would inherit the whole existing machinery for free, but the RDR number is the key the Cpi-Dashboard integration uses and markets have no RDRs of their own. Five rows claiming one RDR means five pool entries and no consistent answer to "how many projects are live". The RDR *is* the project.

*A child table rather than a JSON column.* Cheap to add, but unqueryable, with no per-market history and no per-market dates — losing exactly the auditability this app exists to provide.

*Status rather than stages.* The stated goal is to keep a record of these steps without adding builds and sub-stages; markets exist to be looked at, not to be enforced. Gates, checklists and notifications are what make a stage expensive, and none of them were asked for here.

*Per-market lateness.* Any scheme that reduces several promised dates to one produces false lateness, which would make the health indicator untrustworthy — and an untrusted indicator gets ignored, taking the genuine late projects with it.

## Consequences

- **Fieldwork progress stays project-level.** `fieldwork_snapshots` is unchanged, because the Cpi-Dashboard progress endpoint cannot split completes by country. Markets track workflow state and dates, never completes. This is a deliberate boundary, not an oversight.
- **No `project_market_id` on `project_assignments`.** The same person handles every market, so assignments need no market dimension.
- **Multiple people per role per project needed no schema change.** `project_assignments` has no unique constraint on `(project_id, role_id)`, so two scripters or three QAs on one project were always representable. Only `self_assign` enforces exclusivity, and only for `pm` — one accountable owner, with `is_head_pm_override` for exceptions. What is still missing is a general "assign this person to this project with this role" endpoint; self-assignment is the only path today.
- **`final_delivery_date_locked` stays a project-level lock.** Per-market `due_date` is PM-editable with no lock. Adding a second lock for marginal protection was judged not worth the complexity; if market dates start moving unaccountably, the fix is an `audit_log` entry per change, not another flag.
- At most one `is_primary` market per project is enforced in application code, not by a constraint — MariaDB has no partial unique index.
- Adding an eighth market status is a migration. `APPROVED` is the one state that could reasonably be collapsed into `CLIENT_REVIEW` if the gap between sign-off and launch turns out not to be worth seeing.
