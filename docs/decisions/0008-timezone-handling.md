# 0008 — UTC storage everywhere; convert to local time only at display

## Context

The team spans the UK and Kenya, with people travelling between them. Delivery deadlines are set in UK time by design. The UK observes daylight saving (GMT in winter, BST in summer); Kenya does not (East Africa Time, fixed UTC+3 year-round) — so the UK↔Kenya gap is not a constant, it's 3 hours for part of the year and 2 hours the rest.

## Decision

Every timestamp in the database (every `DateTime` column across the schema — see `architecture.md` §8) is stored as UTC, with no exceptions. Conversion to a specific timezone happens only at the boundary — when a UK-time deadline is entered (converted UK-local → UTC via Python's `zoneinfo`, which carries the real `Europe/London` DST rules) and when a timestamp is displayed to a specific viewer.

Display uses two layers, not one stored "user's timezone" fact:
- The **frontend detects the viewer's actual current browser timezone** (`Intl.DateTimeFormat().resolvedOptions().timeZone`) for anything rendered live in the app — this handles travel automatically, since a traveling user's device already reflects wherever they currently are.
- `users.timezone` (an IANA zone name, e.g. `"Europe/London"`, `"Africa/Nairobi"`) is the fallback for anything generated outside a live browser session — a notification's stored text, a future digest — where there's no browser to ask.

`final_delivery_date` and `expected_field_end_date` are modeled as real `DATETIME` columns, not bare `DATE`, because a deadline "in UK time" carries a specific instant (which DST affects), not just a calendar day.

## Why

Storing local wall-clock time directly is a well-known source of real bugs: the hour UK clocks fall back from BST to GMT happens twice in one day, so a stored local time like "01:30" is genuinely ambiguous without also recording which offset applied at that moment. UTC has no DST and no ambiguity — exactly one correct instant per event, regardless of which region's clock-change rules are in play on that date.

Hardcoding an offset (e.g. "Kenya is UK+3") would be silently wrong for roughly half the year, since it's only true while the UK is on GMT — during BST it's +2. `zoneinfo` (Python's standard library, backed by the IANA tz database) carries the actual rules and gets this right automatically, including the fact that DST transition dates themselves shift slightly year to year.

Treating "the user's timezone" as one fixed, permanently-stored fact would be wrong for anyone travelling — a UK-based user visiting Kenya, or vice versa, would see incorrect local times for the whole trip if the system relied solely on a stored value. Detecting the live browser timezone solves that for anything actually being looked at right now; the stored `users.timezone` only needs to be right often enough to serve as a reasonable fallback for non-interactive cases.

## Consequences

- Every place `datetime.now()` (naive, local-machine time) might be tempting in backend code must instead be `datetime.now(timezone.utc)` or the database's own `server_default=func.now()` (already used throughout `models.py`, which returns UTC as long as the MariaDB server's own session timezone is UTC — worth confirming as part of Slice 0's environment setup, not assumed).
- Any endpoint accepting a "UK time" deadline input must explicitly convert via `zoneinfo.ZoneInfo("Europe/London")` before storing — never store what the client sends as if it were already UTC.
- The frontend needs a small utility (used everywhere a timestamp is displayed) that formats a UTC value using the browser's detected timezone — a single shared function, not reimplemented per page.
