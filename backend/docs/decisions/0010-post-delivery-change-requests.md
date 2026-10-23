# 0010 — Post-delivery change requests tracked separately, not by rewinding the project

## Context

Work arrives on projects that are already delivered and closed off — a client asks for a crossbreak to be included, a retabulation, some additional analysis. This is real work that someone has to do and that currently has nowhere to live.

PMs are the people who receive these requests, but in practice they do not always log them. A record only a PM can create is a record that will sometimes not exist.

## Decision

A `change_requests` table, independent of the stage machinery:

```
change_requests   id, project_id FK, raised_by FK users,
                  title VARCHAR(120), description TEXT,
                  status ENUM (OPEN | IN_PROGRESS | COMPLETED),
                  assigned_to FK users NULL, due_date DATETIME NULL,
                  created_at, completed_at NULL
```

The project stays `DELIVERED` throughout. A change request never moves a project's stage, and open requests appear as a badge on a delivered project rather than as a project that went backwards.

**Anyone holding `pm`, `dp` or `admin` can raise one.** The data team can log requests a PM did not.

No approval gate. These are tracked work items, not a workflow.

**The kind of change is free text, not a fixed vocabulary** — a short `title` plus a longer `description`, both written by whoever logs the request. Dropdown picks may come later; they are not guessed now.

## Why

Pushing the project back to `DATA_PROCESSING` was the obvious alternative and is worse on three counts: it destroys the meaning of `DELIVERED`, it corrupts the cycle-time data being captured for Phase 2 analytics, and it makes `final_delivery_date` ambiguous — delivered in March, or in June?

A crossbreak request is not the pipeline running again. It is a small discrete ask against a finished project, and modelling it as one keeps both facts true at once: the project *was* delivered on time, *and* there is open work on it.

*Free text over an enum.* The four categories in the first draft (crossbreak, retabulation, additional analysis, other) were invented from two examples. A fixed list that is slightly wrong does not merely fail to classify — it actively destroys information, because every request that doesn't fit becomes `other` and the real nature of it survives only if someone bothered to repeat it in the description. Free text costs a `GROUP BY` that won't work cleanly for a while. Narrowing to picks later is a migration plus a backfill driven by titles that genuinely occurred, which is strictly better evidence than a guess made today; and the free text remains as the fallback for anything the eventual list misses.

There is precedent in this schema already — `revisions` records client-review rework rather than rewinding the stage (§5). `change_requests` is the same shape applied after delivery instead of before launch. They are kept as separate tables because the lifecycles, the owners (scripter vs DP) and the reporting are all different; generalising them into one table would mean a column that is meaningless in half the rows.

## Consequences

- **The "whoever notices, logs it" rule is deliberate and worth defending.** The instinct of a future maintainer will be to restrict creation to PMs on tidiness grounds. That would quietly reintroduce the gap this decision exists to close.
- `DELIVERED` remains terminal in the stage model, so no new stage, no new transition type, and `stage_transitions` is untouched.
- Change requests are fully additive — nothing else depends on them, so they can be built whenever there is room in the schedule rather than inside a particular slice.
- Reporting on **volume** ("how much post-delivery work does this client generate?") comes free from the table. Reporting on **type** does not, until titles are categorised — accepted deliberately, since volume is the question being asked today.
- No notification triggers in Phase 1. If requests start going unnoticed, the fix is a notification on assignment, using the existing `notifications` table.
