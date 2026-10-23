# 0001 — Gated-confirm stage transitions, not full automation

## Context

The initial brief proposed fully automatic transitions: the moment the last mandatory checklist item is ticked, the project silently advances to the next stage (e.g. Scripting checklist complete → auto-move to QA).

## Decision

Checklist completion **gates** the transition button (disabled until every mandatory item is ticked or marked N/A), but a human still has to click it. The click is the event that gets timestamped, attributed, and written to `stage_transitions`.

## Why

Full automation trades one failure mode for another. It protects against skipped steps, but introduces a new risk: an accidental last checkbox instantly moves a project out of someone's hands, fires notifications, and appears in the next queue — with no natural moment to catch it. It also erases a genuine distinction: "checklist done" and "I'm ready to hand this over" aren't always the same moment (a scripter may want one more look before releasing).

The confirm click is also a cleaner audit anchor than "system advanced because checkbox 7 was ticked" — it's an intentional handoff, not an implicit side effect.

## Consequences

- Every stage-advancing button needs both a client-side "all items resolved" check and a distinct submit action.
- `stage_transitions` records who clicked, not just what was ticked.
- No loss of the original error-prevention goal — the gate is still mandatory; this only adds a check against the opposite error (premature advancement).
