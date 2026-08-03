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

## Format

A single table per requirements section (Phase 1, Phase 2, Non-Functional — matching `requirements/requirements.md`'s own structure), each row: Requirement | Description | Proven by | Status. Link the "Proven by" cell to the actual feature file and scenario name so the user can open it directly.
