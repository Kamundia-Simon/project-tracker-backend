> **Amended 2026-10-22 — the scripter self-check is a gate, not a reminder.** The team's decision: `send-to-qa` refuses until every item on the scripting checklist is answered. The rest of this ADR still holds for the other checklists.
>
> What changed the call: the scripter self-check is a **declaration**, not an aide-memoire. The paper form it came from ends with a signature confirming the survey is ready for review, and the cost of a bad script reaching QA — or worse, a client — is a revision round and a damaged date. It is also the one checklist whose author is the only person who can honestly answer it.
>
> Two things keep this from becoming tick-to-proceed theatre. Every item can be marked **not applicable** rather than done, so nobody is forced to claim they tested quotas on a survey that has none — the gate asks for a decision on each item, not a yes. And the gate lives at the transition, not on the field: a scripter can save a half-finished checklist as often as they like.
>
> If this starts producing reflexive ticking, the honest fix is fewer items, not a softer gate.

# 0002 — Checklists are static UI reminders, not database-modeled content

## Context

The original brief implied a full checklist subsystem: templates, versioned items, per-item completion records with audit history — mirroring how the paper 3Gem checklists (Scripter Self-Check, Quality A Checklist, Final Data QA Checklist) work today, including per-item sign-off.

## Decision

Checklist item text is hardcoded in the frontend, not stored or managed in the database. Per-project tick-state is persisted as a single JSON column per checklist on `projects` (e.g. `scripting_checklist_state`) so it survives a page refresh — but there is no per-item audit trail and no template/versioning system. The only fact that lands in the audit trail is the single stage-completion event (who clicked "Send to QA," and when).

An item counts as resolved whether ticked complete or marked N/A, matching the paper forms' own ✓/N-A columns — a project with no loops or grids shouldn't get stuck on a loops-and-grids item.

## Why

The checklists are fixed, internally-authored documents that change rarely, if ever. Building a templating/versioning/per-item-audit system for genuinely static content is complexity with no one asking for it — the meaningful audit fact is "scripting was marked complete by Ben at 14:32," not "item 7 was ticked at 14:29 and item 8 at 14:31." If item-level history is ever needed, it can be added later without disturbing the stage-level model.

## Consequences

- No `checklist_templates` / `checklist_items` / `project_checklist_items` tables.
- Updating checklist wording is a frontend code change + deploy, not an admin UI action — acceptable for Phase 1, revisit if checklists start changing often (see `phase-1-plan.md` deferred list).
- Tick-state is per-project convenience data, not compliance evidence; the audit trail's evidentiary weight lives entirely in `stage_transitions`.
