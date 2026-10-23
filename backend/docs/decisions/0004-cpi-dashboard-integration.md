# 0004 — CPI Dashboard is the source of truth for fieldwork data

## Context

Fieldwork completes/target data already exists in `Cpi-Dashboard`'s `points` table, synced from two physical Askia servers via a Java/JDBC process, with per-survey metadata (`meta` table) and IR calculation already built (`services/quotas.py`). This app needs fieldwork progress per project to compute soft-launch flags and fieldwork percentage.

## Decision

`Cpi-Dashboard` gains one new read-only endpoint, `GET /api/external/surveys/{rdr_number}/progress`, returning `{"survey": "<rdr_number>", "completes": int, "target": int, "progress_pct": float}` — built and owned by the user in that codebase, confirmed live and working (`RDR004364` → `{"survey":"RDR004364","completes":2068,"target":2000,"progress_pct":103.4}`, checked 2026-08-18). No `ir` field in the response; `fieldwork_snapshots.ir` stays `NULL` for now. The RDR-keyed path implies `Cpi-Dashboard` already resolves `rdr_number` to a survey internally — exact mechanism not yet reviewed on this side.

This app polls that endpoint on a schedule for each live project and writes a row to `fieldwork_snapshots` each time, rather than querying it live on every page load.

## Why

Re-implementing the dual-server Askia sync and IR calculation in a second codebase would be exactly the kind of duplicated functionality worth avoiding — any future Askia change would need fixing twice, with two chances to drift out of sync. A single dedicated endpoint keeps `Cpi-Dashboard` as the one place that talks to Askia, and this app as a well-behaved read-only consumer.

Snapshots rather than a live proxy give resilience if `Cpi-Dashboard` or Askia is briefly unavailable, and — more importantly — give pacing history: "is this project completing fast enough to hit the field deadline" needs a time series, which a live pass-through alone can't answer.

## Consequences

- This app has a hard dependency on `Cpi-Dashboard`'s `/api/external/surveys/{rdr_number}/progress` endpoint, which now exists and is confirmed working locally.
- If `Cpi-Dashboard` is down, fieldwork figures here go stale but don't error the page — last snapshot stays visible with its timestamp.
- No write access to Askia or `Cpi-Dashboard` from this app at any point (reinforced by 0005).
- Open question, not yet resolved: the `/api/external/` prefix suggests this may need its own service-to-service auth (e.g. an API key) rather than end-user Clerk auth, since the poller calling it isn't a logged-in person. Confirm how that endpoint is (or should be) protected before deploying the polling job anywhere but localhost.
