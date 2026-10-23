# 0007 — Rate limiting and caching, built in from the foundation layer

## Context

Both were originally scoped as ordinary implementation detail, added wherever a slice needed them. The user wants them treated as first-class from the start of the build, not retrofitted after a performance problem or an abuse incident.

## Decision

Add **Redis** to the stack during Slice 0 (foundation), before any feature slice is built, backing two concerns:

**Rate limiting** (via `slowapi`, Redis-backed rather than in-memory — in-memory limiters don't stay consistent once there's more than one uvicorn worker or Docker replica):
- **Inbound:** sensible per-user limits on our own API, particularly write endpoints (stage transitions, comments, bulk actions) — protects against runaway retries or a buggy frontend loop, not really "abuse" for a 20-25 person internal tool, but cheap insurance.
- **Outbound:** the CPI Dashboard polling job (see [`0004-cpi-dashboard-integration.md`](0004-cpi-dashboard-integration.md)) is throttled to a controlled interval per project rather than polling as fast as possible, with backoff on failure — respects `Cpi-Dashboard`'s own capacity rather than treating it as free to hammer.

**Caching** (Redis, short TTLs):
- Dashboard aggregate queries (projects-by-stage, workload-by-user, health breakdown) — these are read constantly (every dashboard load) but only need to be accurate to within a minute or so, not real-time to the second.
- `fieldwork_snapshots` already functions as an application-level cache of `Cpi-Dashboard`'s live numbers in spirit (see 0004) — Redis caching is the same principle applied to our own derived/aggregate data, not a new idea, just a second application of it.

## Why

Stated directly by the user as a standing engineering value, not scoped to one feature — see the `feedback-rate-limiting-caching` memory entry. Practically: dashboard aggregate queries are exactly the kind of read that gets hit on every page load by every user and scales in cost with project count over time, and an unthrottled poller against `Cpi-Dashboard` risks becoming a noisy-neighbor problem for a service this app doesn't own. Doing this in the foundation layer means every later slice inherits it for free instead of each one deciding ad hoc whether to bother.

## Consequences

- Redis becomes a new runtime dependency — needs to exist in local dev, test (Railway), and production (Docker) environments. Add a Redis service to whatever `docker-compose`/Railway config Slice 0 produces.
- Slightly more foundation-layer work up front (Slice 0 grows to include Redis wiring, a `cache.py`/`limiter.py` module, and the polling job's throttling logic) in exchange for not having to retrofit it into every slice that touches an expensive read or an external call.
- Cache invalidation needs care wherever it's used: a dashboard aggregate cached for 60s that doesn't reflect a stage transition made 10 seconds ago is an acceptable tradeoff for a dashboard; it would not be acceptable for `project_assignments` permission checks, which must never be cached (always hit the database — the cost of a stale "yes you can edit this" is not one to risk on this app).
