# 0006 — Build feature-by-feature (vertical slices), not backend-then-frontend

## Context

Prior projects were built backend-first, then frontend. This project has an explicit secondary goal of being a genuine learning exercise, and the user wants to try a different build order.

## Decision

After a one-off foundation layer (auth wiring, base app shells, `users`/`roles`/`project_assignments`), each feature is built end-to-end before the next begins: migration → SQLAlchemy model → Pydantic schema → endpoint → verify in `/docs` → matching React page → wire with TanStack Query → verify in the browser. See `phase-1-plan.md` for the concrete slice order.

## Why

Backend-then-frontend hides the payoff until the whole backend is done, and any awkward API decision doesn't surface until the frontend build is already underway. Building one real feature fully — table to screen — before repeating the pattern gives a complete, working mental model of how a piece of data moves through the whole stack, which suits a learning-focused build better, and also surfaces integration problems (a schema that's awkward from the frontend, a query that doesn't fit the page) one feature at a time instead of all at once at the end.

## Consequences

- Some plumbing (auth, layout, shared tables) has to be built up front regardless, since no feature slice is meaningful without it.
- Slice order matters — later slices depend on earlier ones (Scripting needs a project to exist, Client Review needs Scripting and QA both built). See the ordering in `phase-1-plan.md`.
- Code review/chat explanation happens per slice, not per layer — fits the "explain in chat, then guide the edit" working style also captured in `CLAUDE.md`.
