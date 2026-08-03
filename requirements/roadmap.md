# Roadmap: Candidate Future Slices

This document lists candidate future work — not committed scope. Nothing here is scheduled; each item still needs to go through proper vertical-slice scoping (and, where it involves real product decisions, a grilling session) before it becomes an active slice, the same discipline every slice through 0005 went through.

**How this differs from the repo's other planning docs:**
- `decision-log.md` records decisions already made and grilled. This document is the opposite — things not yet decided or scoped.
- `parking-lot.md` tracks specific items that were surfaced mid-work and deliberately deferred, each with its own status lifecycle (parked/promoted/closed/superseded) and a concrete originating slice. This document is a broader, standing candidate list, not tied to a single originating moment.

Update this list as things get promoted into an actual slice (move the item out, or note it here as done and point at the slice doc) or as new candidates surface.

## Business (Product-Facing)

### Remaining Phase 1 core-loop gaps

- **FR-004 — Treatment trade-off comparison.** Given a described situation, compare applicable treatment options and surface trade-offs (temperature constraints, organic-certification compatibility, withdrawal periods) instead of one unexplained recommendation. Needs a materially richer corpus first — the current corpus has exactly one passage per jurisdiction, not multiple competing treatment options to compare.
- **FR-006 — Source conflict detection.** Surface it explicitly, rather than silently resolving it, when two authoritative sources in the corpus materially disagree. Needs multi-passage retrieval (today's retrieval takes only the single closest match) plus some mechanism for recording which documents actually conflict — likely a manually curated relationship, in the same spirit as FR-005's `superseded_by_corpus_document_id`, rather than automated contradiction detection (consistent with the existing "don't automate ahead of the pain" pattern from the Source Supersession And Conflict Detection decision).

### Capability extensions once Corrections accumulate

- **Corpus Curator-facing Correction review view.** Slice 0005 only built the write path (a Beekeeper submitting a Correction). Nothing yet lets anyone read or triage the Corrections that accumulate.
- **Activate the Correction review gate.** The domain model already reserves `review_pending`/`review_approved`/`review_rejected` statuses exactly for this, per the Correction Trust Level For V1 decision — worth revisiting once there is more than one real user, since the current "every correction is trusted directly" approach was explicitly justified by a population of one.

### Corpus growth

- **Additional jurisdictions.** V1 covers UK and US only; FR-003 explicitly notes EU coverage is deferred and must be modelled at member-state granularity when added, not as a single "EU" jurisdiction.
- **Deeper source documents per jurisdiction.** More than one document/treatment option per jurisdiction is a prerequisite for FR-004 (trade-off comparison) and FR-006 (conflict detection) to have anything real to work with.

### Phase 2 — The Advisor (explicitly out of scope until Phase 1 is trusted)

Per the V1 Scope Boundary decision, none of this begins until Phase 1's grounding and citation behaviour is trusted:

- **FR-009 — Proposed treatment schedule.** Given hive/apiary context and history, draft a proposed treatment schedule and present it for explicit human approval.
- **FR-010 — Treatment history recording.** Record what was applied, when, and at what dose, against a hive's treatment history.
- **FR-011 — Optional HiveSight photo-based mite-count integration.** A data-source relationship only, not an identity/access dependency, per the existing decision.

### Compliance and trust

- **Real user authentication**, replacing the current dev-header approach — a prerequisite for genuine multi-user use, not just multi-user domain modelling (which already exists per FR-000).
- **Activate the `Data Deletion Request` workflow.** Currently a dormant, modelled-but-inert entity per the Retention And Deletion Planning decision — no v1 UI, no enforcement, no scheduled purge.
- **Confirm/configure data retention terms with Voyage AI and Anthropic.** Flagged explicitly in the Retention And Deletion Planning decision as necessary before any deletion workflow can be considered complete, and not yet started — local deletion alone isn't sufficient if Query text is retained on a provider's side under their own terms.

## Technical (Engineering-Facing)

### Deployment and operations

- **Stand up the Fly.io production environment.** Chosen per the Deployment Platform decision, not yet built — no production-like environment exists today, only local dev.
- **CI pipeline.** No `.github/workflows` or equivalent exists yet — the full test suite (Python, Vitest, Playwright) only runs when someone runs it locally.
- **Observability/logging for the API.** Every slice doc through 0005 lists this layer as "Not touched" — there is no logging or monitoring beyond what FastAPI/uvicorn emit by default.

### Retrieval quality

- **Replace the provisional grounding thresholds with a properly calibrated dataset.** The current 0.35/0.55 values (see FR-008 Grounding Classification Mechanism) were calibrated against a handful of manual test queries against two Passages, explicitly documented as provisional everywhere they appear.
- **Passage chunking strategy.** Today, each Corpus Document is exactly one Passage (the whole document). A real corpus with longer source documents will need genuine chunking logic, which doesn't exist yet.
- **Handle Voyage AI's free-tier rate limits properly.** Hit manually during threshold calibration (worked around with a backgrounded script and manual sleeps) — no real rate-limit/backoff handling exists in `VoyageEmbeddingProvider` itself.

### Test infrastructure

- **Durably resolve the stub-vs-real embedding distance-scale mismatch.** Currently solved by giving the stub and real embedding providers separate, environment-configured threshold values (see the Grounding Thresholds Are Environment-Configurable, Not a Single Hardcoded Value decision) — a working fix, but the underlying tension (a crude bag-of-words stub can't track real semantic distance) is still there; a smarter stub or a different testing strategy could remove the need for parallel threshold configs entirely.
- **Component-level UI tests.** Every UI behaviour built so far (grounding banners, citation attribution, correction flow) is verified only through Playwright/Gherkin end-to-end tests and manual browser passes — there's no lighter-weight component-test layer (e.g. Vitest + React Testing Library) for faster, more targeted UI regression coverage.

### Housekeeping

- **Pre-existing ruff import-order nit in `scripts/seed_test_db.py`.** Noticed while working on Slice 0004, left alone since it predates that work and wasn't the file being changed. Trivial one-line fix whenever someone's touching that file anyway.
