---
name: requirements-traceability
description: Maintain requirements/traceability.md, the plain-English mapping from each functional requirement to the Gherkin scenario that proves it. Use this whenever a vertical slice is scoped, when its acceptance criteria are met, whenever a feature file or scenario is added/renamed/removed, and whenever the user asks about test coverage, confidence in refactoring, or "what's actually tested" without wanting to look at code.
---

# Requirements Traceability

The user on this project does not read code and does not want to. Their only way to trust that the system behaves correctly — now, or after some future refactor — is a mapping from each functional requirement straight to the plain-English Gherkin scenario that proves it. That mapping lives in `requirements/traceability.md`. Keeping it accurate is not documentation busywork; it is this user's entire confidence mechanism, stated explicitly by them, so treat it with the same weight as shipping code correctly.

## The rule

No functional requirement counts as "done" until:

1. It has at least one Gherkin scenario in `apps/web/tests/acceptance/features/` proving the behaviour end-to-end (not a unit test standing in for it).
2. `requirements/traceability.md` has a row linking the requirement to that scenario, updated in the same pass as marking the slice's own acceptance criteria complete — not as a follow-up task that might get skipped.

If a slice's acceptance criteria don't include real Gherkin coverage, that itself is a gap worth naming before calling the slice finished, not something to quietly work around.

## Feature files are named by capability, never by slice

`apps/web/tests/acceptance/features/` is organised by capability (`grounding/`, `jurisdiction/`, `provenance/`, `corrections/`, `treatment/`, ...), not by the slice that introduced the behaviour. This is deliberate, not cosmetic: slice docs are point-in-time records, and behaviour genuinely gets superseded by later slices without the earlier slice doc being retroactively rewritten. A file named `vertical_slice_0004_...feature` gives no signal to a future reader (human or AI) about whether it's frozen historical evidence or still the live description of current behaviour — a capability-named file makes that unambiguous by construction. When a new slice adds acceptance coverage, put it under the capability directory it belongs to (create one if it's new), never under a slice number. If a slice number appears anywhere in a feature or step filename, that's a naming regression to fix, not a style choice to leave alone.

## When to touch the traceability doc

- A vertical slice's acceptance criteria are all met and its Gherkin scenarios are verified passing: add or update the row(s) for the requirement(s) it proves.
- A feature file or scenario is renamed, split, merged, or removed: update the doc immediately so it never silently points at a scenario that no longer exists.
- A requirement is scoped but deliberately not yet built (e.g. blocked on missing content, or explicitly deferred to a later phase): still add a row, marked as not-yet-covered with the real reason — an honest gap is more useful to this user than an absent row they'd have to notice is missing.
- The user asks anything shaped like "what's tested," "can I trust a refactor here," "how confident are we in X" — answer by pointing at this doc's relevant row(s) first, before reaching for unit-test internals they didn't ask for and don't want to parse.

## What belongs in the doc, and what doesn't

- One row per requirement, not per scenario. A requirement proven by more than one scenario (e.g. a Scenario Outline with multiple Examples) still gets a single row — list every scenario that matters, but don't fragment one requirement across several rows.
- Plain status, always one of: covered (name the scenario), not yet covered (name the real blocking reason), deferred (name the decision that deferred it), or architectural property / not scenario-testable (say why a runtime scenario wouldn't make sense for this one).
- Never list unit or integration test file names here. Those are pytest/Vitest — the implementer's safety net for fast feedback and precise regression detection, not something this user is expected to read or trust directly. Putting them in this doc would defeat its entire purpose: it exists specifically as the one place this user can go without opening a code-literate artifact.
- Never duplicate implementation detail (which repository method, which prompt, which threshold value) into this doc. That belongs in the vertical-slice docs (`architecture/vertical-slice-*.md`) and the decision log — link to those rather than restating them here.
- Be honest about what a "Covered" row actually proves. If the acceptance suite runs on stub providers rather than the real AI integration, say so once, clearly, rather than letting "Covered" imply more real-world confidence than the tests actually give.

## Choosing the right proof seam, not defaulting to Gherkin

Browser-level Gherkin is the default proof seam, but it is not always the *right* one, and forcing a claim into it anyway can do real damage. Two concrete cases already hit in this project:

- **Shared process state.** The acceptance suite runs every scenario sequentially against one shared server process. A claim that depends on process-wide state (a rate limiter, a singleton counter) can't be proven at browser level without either poisoning every other scenario's state in the same run or standing up a second, fully isolated config for one scenario. Prove it at the unit/integration seam instead, with a scoped dependency override — see Slice 0013.
- **External providers that can't be automated.** A real third-party consent flow (Google sign-in, an OAuth screen) cannot be driven by Playwright without either scripting the provider's own UI (brittle, and not this project's dependency to own) or adding a test-only bypass to production code so the app *thinks* it's signed in. The bypass is the one move to reject outright — it is a real, if narrow, security-relevant code path added purely for test convenience. Accept the coverage move instead: prove what the browser genuinely can prove (the sign-in *gate* itself), and prove full behaviour at the pytest/`TestClient` seam — see Slice 0014.

When this happens: don't quietly drop coverage, and don't force it into the wrong seam either. Name the constraint explicitly in the slice doc's Test Seams/Open Questions section and in the relevant `traceability.md` row, so a future reader sees *why* a requirement is proven where it is, not just that it is. A reduction in browser-level coverage forced by a real constraint like this is an honest trade-off worth surfacing to the user as its own decision, not something to resolve silently.

## Format

A single table per requirements section (Phase 1, Phase 2, Non-Functional — matching `requirements/requirements.md`'s own structure), each row: Requirement | Description | Proven by | Status. Link the "Proven by" cell to the actual feature file and scenario name so the user can open it directly.
