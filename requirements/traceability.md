# Requirements Traceability

This document exists so you can verify test coverage without reading any code. Every functional requirement is mapped to the plain-English Gherkin scenario that proves it — open the `.feature` file named here, and you're reading the actual specification the system is held to, in the same language as `requirements.md`.

**What this deliberately excludes**: unit and integration test file names (pytest, Vitest). Those exist for the implementer's benefit — fast feedback, precise regression detection — not as something you're expected to read or trust directly. Mixing them into this table would defeat the point of having it. If you want the full unit/integration picture, ask for a coverage report; this doc is only about the layer built for you.

**One honest caveat that applies to every "Covered" row below**: the acceptance suite runs against stub embedding/generation providers (fast, free, deterministic), not the real Claude/Voyage APIs. It proves the *mechanics* are correct — retrieval, classification, citation, UI rendering — end-to-end. It does not continuously prove the real AI integration behaves well; that's currently only checked by manual live-browser demos during each slice's implementation, which aren't automated or repeatable. See the "Real-provider behaviour" section at the bottom.

**Mechanism note (2026-08-07, Slice 0013)**: `POST /queries` no longer requires the dev-header/`workspace_id` shown implicitly in every scenario below — it's unauthenticated (Guest access, IP-rate-limited) by design now, not a leftover gap. Every scenario below already exercises this path since it's the only path that exists. Guest rate-limit-exceeded behaviour is proven at the `RateLimiter` unit and `POST /queries` pytest seams, not a Gherkin scenario — see `architecture/vertical-slice-0013-guest-access-and-rate-limiting.md`'s Open Questions for why a shared-process singleton made that seam the wrong one for this claim.

## Phase 1: Grounded Knowledge

| Requirement | Description | Proven by | Status |
|---|---|---|---|
| FR-000 | Model `Workspace`/`Workspace Membership`/roles | *(implicit)* | ⚪ Not a discrete scenario — every scenario's precondition depends on a valid dev-authenticated Workspace Membership already existing, so it's exercised constantly but never asserted on its own |
| FR-001 | Answer grounded in the curated corpus, not unaided generation | `grounding/grounded-query-answer.feature` — *Beekeeper asks a Varroa question and receives a grounded, cited Answer* | ✅ Covered |
| FR-002 | Every answer cites its source passage(s) | Same scenario as FR-001, plus every other scenario below (citations are asserted throughout) | ✅ Covered |
| FR-003 | Determine jurisdiction; never blend guidance across jurisdictions | `jurisdiction/jurisdiction-isolation.feature` — *Beekeeper receives an Answer grounded only in the selected Jurisdiction* (Scenario Outline, both UK and US examples) | ✅ Covered |
| FR-004 | Compare treatment options, surface trade-offs | `treatment/treatment-trade-off-comparison.feature` — *Beekeeper asks a question spanning multiple genuinely relevant treatment options* | ✅ Covered — briefly flagged failing on 2026-08-07 (a test-timing bug, not a product issue; fixed same day, see `requirements/roadmap.md`) |
| FR-005 | Flag a source that's been superseded, rather than citing it as current | `provenance/source-supersession-and-provenance.feature` — *Beekeeper's Answer cites a source that has since been superseded* | ✅ Covered |
| FR-006 | Surface it explicitly when two authoritative sources materially disagree | — | ❌ Not built — no scenario exists. Blocked on finding or surfacing a genuine source disagreement; see `requirements/roadmap.md` |
| FR-007 | Beekeeper can flag an Answer as wrong; retained as evaluation evidence | `corrections/user-corrections.feature` — *Beekeeper flags a grounded Answer as wrong* and *Beekeeper flags an ungrounded Answer as wrong* | ✅ Covered |
| FR-008 | No unaided-generation answers when nothing is grounded; say so, offer partial match if any | `grounding/no-grounding-behaviour.feature` — *Beekeeper asks a question only loosely related to the seeded Passage* and *...unrelated to the seeded Passage* | ✅ Covered |

## Phase 2: The Advisor

| Requirement | Description | Proven by | Status |
|---|---|---|---|
| FR-009 | Draft a proposed treatment schedule, await human approval | Slice 0008's four scenarios (`tests/test_hivesight_integration_router.py`), Slice 0009's four reject-and-revise scenarios (`tests/test_hivesight_rejection_router.py`), and Slice 0011's six contract-readiness scenarios (`tests/test_treatment_plan_readiness_router.py`) — all API-level, `TestClient`, no browser, since HiveSight is this flow's only UI. Each test's docstring quotes its exact scenario text. Covers: grounded recommendation + suggestion recorded; unauthorized request rejected; no-grounding honesty preserved; completion confirmation resumes and closes the loop; rejection produces a revised, superseding suggestion; repeated rejection exhausts a capped revision limit without losing the last suggestion's acceptability; rejecting with nothing suggested is rejected; a revision that itself comes back ungrounded is reported honestly, distinct from exhaustion; jurisdiction-code resolution and audit fields (`contract_version`, `answer_id`); idempotent repeat-request handling for both the still-pending and already-completed cases | ✅ Covered — for the Advisor's own side only. HiveSight's real endpoints (accept-suggestion, completion webhook, rejection webhook) don't exist yet; these slices prove the Advisor's side against stubs/test-only stand-ins. See `hivesight-advisor-integration-contract` skill for current cross-app status |
| FR-010 | Record treatment history | — | ⚪ Superseded — this responsibility moved to HiveSight (system-of-record split, `requirements/roadmap.md`, 2026-08-04); nothing to test on the Advisor side |
| FR-011 | Optional HiveSight photo-based mite-count integration | — | ⚪ Deferred — still not built; widened in scope (inspection *history*, not a single reading) per the FR-009 discussion in `requirements/roadmap.md` |

## Non-Functional

| Requirement | Description | Proven by | Status |
|---|---|---|---|
| NFR-001 | Never present output as an official diagnosis/prescription | — | ⚠️ Not explicitly tested — no scenario or copy-assertion currently checks this framing. Worth a scenario if this becomes a real risk (e.g. once Phase 2 exists) |
| NFR-002 | Phase 1 vs. Phase 2 output visibly distinguished | — | ⚪ Not yet applicable — Phase 2 doesn't exist yet, so there's nothing to distinguish from |
| NFR-003 | Source documents carry provenance/licence metadata | `provenance/source-supersession-and-provenance.feature` — *Every Answer displays its citation's provenance* | ✅ Covered |
| NFR-004 | Never require HiveSight to be installed/in use | — | ⚪ Architectural property, not scenario-testable — verified by design (Advisor Independence From HiveSight decision: separate service, separate repo, separate database), not by a runtime test |

## Real-Provider Behaviour

The rows marked "Covered" above are proven mechanically (stub providers) on every CI run. Real-AI-behaviour confidence — does Claude/Voyage actually produce good grounded answers, comparisons, and citations against real content — comes from two places:

- Live contract tests (pytest, skipped in CI without API keys): `test_generation_claude_live.py`, `test_embedding_voyage_live.py`, `test_corpus_review_claude_live.py`. These are code-literate, not something you're expected to read directly.
- **`pnpm test:acceptance:live`** — runs a small, hand-picked subset of the same Gherkin scenarios above (grounded citation, no-grounding, comparison) against the real Voyage/Anthropic APIs and the real dev database, instead of the stub providers. Not part of the default CI path — it costs real API calls and isn't fully deterministic — run on demand when real-behaviour confidence matters, not just mechanical confidence.

**First real run already earned its keep.** It surfaced that the grounding thresholds (0.35/0.55) have drifted since they were calibrated: the "unrelated question" example in the no-grounding scenario now measures a real distance of 0.4548 against the grown UK corpus — ambiguous "partial" territory, not clearly `ungrounded` — because the corpus has grown from one UK document to four since calibration. This is a genuine, reproducible finding (verified deterministic, not LLM noise), not a test bug. The working theory that passage chunking (`architecture/vertical-slice-0012-passage-chunking.md`) would fix this was tested once chunking landed and did not hold — re-measurement showed off-topic queries moved closer to the grown corpus, not further. Nothing has crossed into a false `grounded` classification, so behaviour is still safe, but there is currently no known fix, only an open problem. See `requirements/decision-log.md`'s two 2026-08-07 entries and `requirements/roadmap.md`.

## Keeping This Current

No functional requirement is "done" until it has a Gherkin scenario and a row in this table — see the `requirements-traceability` skill for the standing rule.
