# 0003 — Database-driven RBAC, Clerk for authentication only

## Context

`Cpi-Dashboard` (sibling project, same org) authorizes access via env-var email lists (`COSTING_ALLOWED_EMAILS`, `PM_EMAILS`, `RECONCILE_ADMIN_EMAILS`) checked in FastAPI dependencies, on top of Clerk for login. Its own code comments note that reconcile-endpoint gating is UX-only, not enforced server-side.

## Decision

Clerk handles authentication only (who is this user). Authorization is entirely our own: a `roles` lookup table (fixed seed data — Admin, PM, Scripter, QA, DP, Viewer) and a `project_assignments` table (`project_id`, `user_id`, `role_id`) recording who currently holds which role on which project. A small backend policy module maps `(role, action)` to allowed/denied; every mutating endpoint checks it directly, never relying on the frontend hiding a button.

## Why

This app's permissions are per-project and change constantly (self-assignment, reassignment) — an env var can't express "user X owns the scripter role on project 47 today." Editing an env var also means a redeploy just to onboard someone to a new project, which doesn't fit day-to-day use. And the CPI Dashboard gap (UI-only gating on reconcile endpoints) is a real risk worth not repeating: authorization belongs on the endpoint, not the button.

## Consequences

- `project_assignments` rows are never deleted, only closed out (`unassigned_at` set) — assignment history is free.
- Adding a new role or permission rule is a backend code change, not a database migration to a permissions table — deliberately simple for ~20-25 users; revisit only if the permission matrix needs to be admin-editable (see `phase-1-plan.md` deferred list).
- **There is a development-only authentication bypass in `auth.py`.** Setting both `ENVIRONMENT=development` and `DEV_AUTH_EMAIL=<address>` in `.env` skips Clerk verification entirely and authenticates every request as that address. It exists because Clerk session tokens expire in ~60 seconds, which makes manual endpoint testing in `/docs` impractical. It requires both variables set, logs a warning on every request, and lives only in gitignored `.env` — but it is a genuine auth bypass, and neither variable belongs in any deployed environment.
- `final_delivery_date_locked` uses the same pattern: a boolean flag (`is_head_pm_override`) on the user, not a hardcoded name, so the override can move to a deputy later without a schema change.
