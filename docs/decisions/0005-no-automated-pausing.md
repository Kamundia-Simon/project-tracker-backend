# 0005 — No automated fieldwork pausing; soft launch is notification-only

## Context

Soft launch (fielding to ~10% of target before full launch, to catch data-quality issues early) is a real step that's easy to forget. One option considered was using Askia's API (already used read-only by `Cpi-Dashboard`) to automatically pause a survey once the soft-launch threshold is reached, forcing a resume click — a hard technical gate.

## Decision

No automated pausing, ever. A scheduled job compares live completes (via `fieldwork_snapshots`, see 0004) against a soft-launch target frozen at 10% of the total target when the project went live. At the threshold, the project is flagged `Soft Launch Due`; the PM manually ticks "Soft Launch Reviewed" to move on. If unreviewed past a grace window (default 24h), the flag becomes `Soft Launch Overdue` — visible, not blocking.

## Why

Explicit decision: this app should never take a write action against live fieldwork. A missed review is a visible, correctable process gap; an incorrectly-paused live survey is a fielding incident with real cost. The asymmetry in downside risk rules out the hard-gate option even though it was technically feasible.

## Consequences

- Soft-launch compliance depends on someone acting on the flag — this is a deliberate tradeoff, not an oversight.
- The soft-launch target is frozen at launch time so a later correction to the project's overall target doesn't retroactively move the goalposts.
- If this proves insufficient in practice, the next step up is a louder escalation (e.g. notify Head PM if overdue by N hours) — still notification-only, before automated pausing would ever be reconsidered.
