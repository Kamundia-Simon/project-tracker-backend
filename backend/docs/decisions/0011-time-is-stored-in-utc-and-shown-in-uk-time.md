# 0011 — Time is stored in UTC and displayed in UK time

## Context

Every commitment this app tracks is quoted to clients in **UK time** — a scripter's ETA ("Thursday 15:00"), a market's due date, a field close, a delivery date. The operations team sits in **Kenya (UTC+3, no DST)**, so the clock on their laptops is never the clock the promise was made on. The UK itself shifts between GMT and BST, so the offset is 2 hours for part of the year and 3 for the rest.

Three things in the original code made this unsafe:

- `server_default=func.now()` on every timestamp returns the **database server's** local time, which depends on how the container or host is configured and is not visible anywhere in the code.
- `datetime.now()` in application code returns the **application host's** local time — a second, different clock writing to the same columns.
- MariaDB `DATETIME` carries no zone, so a stored value has no way to say which clock produced it.

Mixed-clock timestamps do not announce themselves. They produce a project that looks three hours late, a "due today" row that appears a day early, and an audit trail whose ordering is wrong only for events near midnight.

## Decision

**Store UTC. Display UK time. Compute day boundaries in UK time.**

- All datetimes are stored as UTC. Application writes go through `clock.utcnow()`; server defaults use `utc_timestamp()`.
- `clock.BUSINESS_TZ = ZoneInfo("Europe/London")` is the single definition of "the zone our commitments are quoted in". It is a named zone, not a fixed `+01:00`, so BST is handled by the zone database rather than by us.
- The API speaks ISO-8601 **with an offset** in both directions. Never a bare `2026-10-23T15:00`.
- The interface shows UK time everywhere, labelled once per screen ("all times UK"), with no per-user conversion.
- Anything derived from a date — *today*, *overdue*, *due this week*, *next two days* — is computed against the current time in `BUSINESS_TZ`, never the viewer's clock and never the server's.

## Why

*Why not show each person their local time?* It was considered and rejected by the team. The number that matters operationally is the one the client was told; showing a Nairobi PM "18:00" when the client was promised "15:00" means every conversation needs a mental conversion, and the two numbers eventually get mixed up in an email. One clock that everyone shares is less sophisticated and harder to get wrong.

*Why store UTC rather than London time?* London time is not monotonic — 01:30 happens twice in October and never in March. Durations, ordering and "how long did this stage take" all break across those two hours. UTC is the only representation where arithmetic is always valid; the display zone is a presentation concern applied at the edge.

*Why a named zone rather than an offset?* `+01:00` is correct for about half the year. A hardcoded offset is a bug with a six-month fuse.

## Consequences

- **`users.timezone` is deliberately dormant.** The column exists and is returned by `/api/me`, but nothing uses it. It is the hook if the team ever spans zones; it should not be wired into display without revisiting this decision.
- **`datetime.now()` is banned in application code.** `clock.utcnow()` is the only source of the current time, which makes the rule greppable: `datetime.now(` should return no hits under `backend/`.
- Server defaults are `utc_timestamp()` rather than `now()`, so a row inserted outside the ORM — a migration, a seed, a manual fix — still lands in UTC.
- **The frontend formats, it does not convert by guesswork.** Rendering uses the `Europe/London` zone explicitly (e.g. `Intl.DateTimeFormat` with `timeZone: "Europe/London"`), never the browser's default, which would silently be EAT.
- Storing UTC while displaying one fixed zone looks like an inconsistency to anyone reading the database directly. This ADR is the answer to "why is this three hours off what the screen said".
- If the team ever spans timezones for real, the change is at the display edge only: the stored data is already correct.
- **`tzdata` is a hard dependency, not an optional one.** `zoneinfo` reads the operating system's timezone database, which Windows does not have and the slim Linux container images omit. Without the package, `ZoneInfo("Europe/London")` raises `ZoneInfoNotFoundError` at import and the app does not start. It is in `requirements.txt` for that reason; do not prune it as unused because nothing imports it by name. The failure is loud and immediate, which is the right trade for a dependency this small.
