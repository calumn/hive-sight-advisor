# AI-SDLC Observations

This document records how AI contributes to the requirements phase and later SDLC phases, continuing the practice established on HiveSight — with the explicit intent of keeping it updated past day one this time.

## Observation Log

### 2026-07-31 Initial Scope Synthesis

Human input (conversation with Claude) established the product direction: a generative-AI product for beekeepers, deliberately sequenced as a grounded-knowledge phase (RAG) followed by an agentic advisor phase, distinct from and complementary to HiveSight's predictive-AI photo analysis.

AI contribution:

- Surveyed the public data landscape for Varroa/bee-health sources across US, UK, and EU jurisdictions to confirm sufficient grounding data existed before committing to the domain.
- Proposed a menu of candidate capabilities across both phases, informed by that data landscape, for the human to react to and scope.
- Synthesized the resulting direction into a draft `vision.md` and `requirements.md`, explicitly marked as unconfirmed and flagged with open questions rather than presented as settled.

Human judgment still required (carried into grilling):

- Confirm or revise v1 scope boundary between Phase 1 and Phase 2.
- Confirm intended user persona(s).
- Confirm jurisdiction granularity for v1.
- Confirm no-grounding behaviour.
- Confirm intended source and trust level of Phase 1 corrections.

### 2026-07-31 Grilling Round Closed

Human-confirmed decisions (all via one-question-at-a-time grilling, per `productivity-grilling`):

- V1 scope is Phase 1 only; Phase 2 explicitly deferred.
- `Workspace`/`Membership`/roles modelled like HiveSight from day one; authentication still deferred. This corrected the AI's first recommendation, which had assumed a permanently single-user tool — the human caught this and it was folded in as an amendment, not treated as a new open question.
- Advisor is architecturally independent of HiveSight; HiveSight is an optional Phase 2 data source only, not an identity/access dependency. A commercial tie-in later is possible but explicitly deferred as a business decision.
- V1 jurisdiction scope is US and UK; EU deferred and must be modelled at member-state granularity when added, not as one bucket.
- No-grounding behaviour: state explicitly when nothing is grounded, offer partial matches if any exist, never answer from unsourced general knowledge.
- Corrections trusted directly for v1 (population of one, and the one user is the domain expert); review-gate concept kept in the domain model for when that stops being true.

AI contribution:

- Proposed a recommended answer for every question, reasoned from decisions already confirmed earlier in the same session rather than from scratch each time (for example, deriving the jurisdiction-scope recommendation from the already-confirmed FR-003 requirement, and the no-grounding recommendation from the already-confirmed FR-002 citation requirement).
- Updated `vision.md`, `requirements.md`, and `decision-log.md` after each confirmed answer rather than batching updates to the end.
- Caught and corrected its own drafting mistake mid-session (a requirement referenced a nonexistent `FR-000` before that requirement had actually been written) rather than leaving the dangling reference.

Every "human judgment still required" item from the initial entry is now resolved. Next phase is architecture (domain model, system context) or a first vertical slice, human's call.

### 2026-07-31 Architecture Pass: Domain Model And System Context

Human direction: proceed to architecture (domain model and system context), with an explicit constraint that the domain model must align with HiveSight's own, and certainly not contradict it, even though the two products are architecturally independent.

AI contribution:

- Re-read HiveSight's current `CONTEXT.md`, `architecture/domain-model.md`, and `architecture/system-context.md` in full before drafting anything, since HiveSight had moved on substantially since the last full review (now at Slice 0015, with terminology changes such as Draft Annotation having been renamed to Candidate Annotation, and a Source Image/Inspection Photo split introduced).
- Produced `CONTEXT.md` for this product structured explicitly around three categories — terms reused unchanged, terms reused but reworded for this product's subject matter, and terms deliberately not imported yet — so every alignment decision is visible rather than left for a reader to infer.
- Produced `architecture/domain-model.md` and `architecture/domain-model-diagram.md`, cross-referencing HiveSight's model at every point of overlap (Workspace, User, Workspace Membership, Internal Capability, the Dataset Curator/Corpus Curator pattern, the User Correction/Correction pattern, the Model Version/Answer Generation Version pattern).
- Produced `architecture/system-context.md`, explicitly reasoning about why it does *not* copy HiveSight's two-service split (no asynchronous long-running job exists here to justify it) rather than mirroring HiveSight's shape by default.
- Caught a real terminology collision during the cross-check — HiveSight's `CONTEXT.md` already reserves `advisor` as a future Workspace Membership role name, a different concept from this product's own name — and logged it as an observation rather than silently ignoring it or over-reacting with an unnecessary rename.

Human judgment still required:

- Every item in `architecture/domain-model.md`'s and `architecture/system-context.md`'s Open Architecture Questions sections (application surface, embedding/generation providers, service split, storage, ingestion triggers) — none of these were decided, all were deliberately left open rather than guessed at.

### 2026-07-31 Architecture Grilling Round 2: Application Surface Through Retention Planning

Human direction: continue the grilling session, one question at a time, through the remaining Open Architecture Questions.

Human-confirmed decisions:

- V1 application surface is a web app backed by a real API.
- Service topology is one live service (Advisor Service); Corpus Ingestion is a curator-run script, not a deployed service.
- Generation and embedding providers are Claude and Voyage AI respectively — the human asked what "embedding" means before re-confirming, a genuine clarifying question rather than a decision, answered directly rather than deferred to a document.
- Database technology is one Postgres database with `pgvector`.
- Jurisdiction resolution is explicit, required UI selection (US/UK toggle), no inference from Query text.
- Source Supersession and Source Conflict detection are both manual Corpus Curator judgement at ingestion time.
- Retention/deletion policy remains explicitly deferred, but the human gave a standing instruction not to leave it as a bare TBD: "at least plan for it, because from the past trying to retroactively fit compliance to these sorts of policies can be a problem." This produced a dormant `Data Deletion Request` entity in `architecture/domain-model.md`, modelled on HiveSight's own entity of the same name for consistency, plus an explicit flag that local deletion alone does not satisfy third-party (Voyage AI, Claude) data retention on Query text — a separate integration task from the deletion workflow itself.

AI contribution:

- Proposed a recommended answer for every question, each reasoned from a `sdlc-architecture-codebase-design` principle already in use elsewhere in the project (the "two-adapter rule" for service topology; "don't automate ahead of the pain" reused verbatim across jurisdiction resolution, database technology, and source conflict detection) rather than treating each question as unrelated.
- Updated `decision-log.md` after each confirmed answer, and updated `domain-model.md`/`domain-model-diagram.md`/`system-context.md`'s Open Architecture Questions sections to strike through resolved items with a cross-reference, keeping documents mutually consistent as the session proceeded rather than batching updates to the end.
- On the retention/deletion instruction specifically, distinguished "the policy is decided" from "the model is ready for the policy" in the Open Architecture Questions wording, rather than marking the item fully resolved when only the second is true — this is the same class of care as the earlier self-caught `FR-000` dangling-reference mistake: writing a forward reference to this very decision-log entry inside `domain-model.md` and then treating that entry's creation as a required, non-optional follow-up rather than an afterthought.

- Deployment platform is Fly.io, for both the Advisor Service and Postgres/`pgvector`, confirmed after a dedicated cost-comparison pass (Fly vs. Render vs. AWS/GCP) rather than on architecture fit alone — the human asked for cost implications before confirming, so the AI researched current 2026 pricing rather than relying on possibly-stale training knowledge.

This closes every item in `architecture/domain-model.md`'s and `architecture/system-context.md`'s Open Architecture Questions sections.

AI contribution (cost pass):

- Searched current Fly.io and Render pricing rather than answering from memory, since hosting prices change and the human's question was explicitly about present-day cost.
- Distinguished hosting cost (platform-dependent, roughly comparable across Fly/Render/AWS at this scale) from usage-based provider cost (Claude generation, Voyage AI embeddings — scales with query volume, tracked separately, not a factor in the platform decision) so the two weren't conflated in the comparison.

### 2026-07-31 Vertical Slice 0001: Definition, Grilling, And Implementation Planning

Human direction: define a few first-slice options, then start implementation planning, per `sdlc-delivery-vertical-slice-planning`.

AI contribution:

- Proposed four slice options (stubbed-corpus Q&A, ingestion-only spike, full real thin slice, no-grounding path first), reasoning each against the requirements it would prove and the technical risk it would retire, and let the human choose rather than picking unilaterally.
- Human chose the stubbed-corpus Q&A option (hand-seeded Passage, real retrieval/generation/citation loop, ingestion pipeline deferred). Wrote `architecture/vertical-slice-0001-grounded-query-answer-with-seeded-corpus.md` per the skill's required structure.
- Surfaced two open questions the slice doc could not resolve alone (real vs. stubbed Claude calls in automated tests; checked-in seed script vs. one-off insert), each with a stated recommendation, grilled one at a time, and logged both as a single decision-log entry (Slice 0001 Test And Seed Approach) once confirmed — the human's stated preference for avoiding unnecessary spend directly shaped the first decision.
- Read HiveSight's actual repo layout, `pyproject.toml`, and `docker-compose.yml` on disk before writing the implementation plan, rather than assuming a stack — confirmed FastAPI/pytest/pytest-bdd/ruff/psycopg on the Python side and pnpm/Vite/React/TS on the web side, and deliberately did not carry over HiveSight's Redis/MinIO services since neither has a justified use in this architecture (no async job, no binary object storage).
- Wrote `architecture/implementation-plan-vertical-slice-0001.md`: one-time scaffolding, a proposed module layout, dependency-injection seams (each already justified by two real adapters — production and stub — per the two-adapter rule), and a TDD red-green sequence ordered by dependency, ending in an end-to-end acceptance test matching HiveSight's `test_vertical_slice_NNNN_bdd.py` convention.

Human judgment still required:

- Approve the implementation plan itself, or adjust before the first red-green cycle (health check) begins.

### 2026-08-02 Vertical Slice 0001: Scaffolding And First TDD Cycle

Human direction: proceed with the implementation plan.

AI contribution:

- Built the one-time scaffolding from the plan: `services/advisor-api/pyproject.toml` (modelled on HiveSight core-api's, with this project's actual dependencies — `anthropic`, `voyageai`, `pgvector` — swapped in), a typed `settings.py`, `docker-compose.yml` using `pgvector/pgvector:pg16` (not plain `postgres:16`), and `.env.example`.
- Found a stale, broken local Python environment (`.venv-advisor-api`, Python 3.10 from an earlier abandoned attempt) that didn't match the `pyproject.toml` requirement of Python 3.12+; recreated it against the correct interpreter rather than debugging the mismatch in place.
- Ran the first TDD cycle (health check) red-before-green: wrote `tests/test_health.py` against a not-yet-existing `main.py`, confirmed it failed for the expected reason (`ModuleNotFoundError`), then wrote the thin `main.py` app factory and confirmed it passed. `ruff check` clean.

Human judgment still required:

- Nothing blocking; next cycle (corpus repository / pgvector retrieval seam) needs a running Postgres (`docker-compose up postgres`) since it's an integration test against a real database, not stubbed.

### 2026-08-02 Vertical Slice 0001: Corpus Repository / pgvector Retrieval Cycle

Human direction: bring up the database, then continue.

AI contribution:

- HiveSight's own Postgres container already held port 5432; rather than touch that project's container, moved this project's `docker-compose.yml` and default `DATABASE_URL` to port 5433, since the two products are meant to run independently and side by side.
- Chose `voyage-3-large`'s 1024-dimension output for the `passages.embedding` column, matching the Generation And Embedding Providers decision, since that's the currently recommended Voyage model.
- Wrote a HiveSight-style numbered-SQL migration runner (`db.py`, `migrations/0001_slice_0001_corpus.sql`) covering only `jurisdictions`, `corpus_documents`, and `passages` — deliberately not `workspaces`/`users`/`queries`/etc. yet, since those aren't needed until later cycles (schema grows one migration at a time, same discipline as the TDD sequence itself). Followed the slice doc's minimal Data Shape list over the fuller domain-model field list for now.
- Ran the retrieval cycle red-before-green: wrote `test_corpus_repository.py` against a real Postgres/pgvector test database (seeding two passages with distinct embeddings, asserting the nearer one is returned), confirmed it failed on a missing module, then implemented `CorpusRepository.find_similar_passages`.
- Hit and fixed one real pgvector/psycopg issue along the way: an untyped query parameter compared against a `vector` column raised `operator does not exist: vector <=> double precision[]` — fixed with an explicit `%s::vector` cast in the query, since the driver has no column-type context to infer from in a bare `ORDER BY` expression the way it does for an `INSERT`.
- `ruff check` clean; both tests (health, corpus repository) passing.

Human judgment still required:

- Nothing blocking; next cycle (embedding adapter seam — stub first, Voyage live test separate) can proceed.

### 2026-08-02 Vertical Slice 0001: Embedding Adapter Seam

Human direction: continue.

AI contribution:

- Defined the `EmbeddingProvider` seam as a `Protocol` in its own module (`adapters/embedding_provider.py`) rather than folding it into either adapter file, so neither adapter has to import from the other and both depend only on the shared contract.
- Ran the stub adapter cycle red-before-green: `StubEmbeddingProvider` is a deterministic hash-based vector (same text → same vector, different text → different vector), covering the actual seam requirement (a real, reusable contract for tests) without needing network access.
- Wrote the production `VoyageEmbeddingProvider` alongside it, explicitly requesting `voyage-3-large`'s output at 1024 dimensions to match the `passages.embedding` column from the previous cycle, rather than trusting a model default that could silently drift.
- Per the plan's explicit deferral ("the Voyage adapter's contract test can be a separate, explicitly-marked live test"), added that live test gated with `@pytest.mark.skipif(not os.getenv("VOYAGE_API_KEY"), ...)`, matching HiveSight's own convention for real-provider integration tests (`test_postgres_persistence_slice.py`). It skips by default and only runs if a real key is exported.
- 3 passed, 1 skipped (the live test, correctly, since no key is set), `ruff check` clean.

Human judgment still required:

- Nothing blocking. Next cycle is the generation boundary seam (`GenerationProvider.generate_answer`, tested against `generation_stub.py` per the Slice 0001 Test And Seed Approach decision).

### 2026-08-02 Vertical Slice 0001: Generation Boundary Seam

Human direction: continue; also asked which Claude model ID to default to and whether prompt caching mattered here.

AI contribution:

- Checked current Anthropic model guidance before hardcoding an ID rather than trusting training-data defaults (models change fast): the guidance is to default to Claude Opus 5 and treat cost tuning as `effort`/thinking configuration, not a smaller model — never silently downgrade model choice for cost, since that's the human's call. Set `output_config.effort: "low"` on the production adapter instead, since grounded-QA-over-one-short-passage is a genuinely low-effort task.
- Checked whether prompt caching was worth adding for this seam: concluded no, since Claude Opus 5's minimum cacheable prefix (512 tokens) is larger than this adapter's system prompt, so a cache breakpoint here wouldn't actually take effect at this scale. Left it out rather than adding inert complexity.
- Used `output_config.format` (structured JSON output: `answer` + `cited_passage_ids`) for the production adapter instead of parsing citations out of free text — more reliable than regex/string matching for a field the rest of the system depends on (Citation persistence, next cycle).
- Ran the stub cycle red-before-green as with the other seams; wrote the production `ClaudeGenerationProvider` and a live contract test gated the same way as Voyage's (`skipif` on `ANTHROPIC_API_KEY`), consistent with the Slice 0001 Test And Seed Approach decision.
- 4 passed, 2 skipped (both live tests, correctly, with no keys set), `ruff check` clean.

Human judgment still required:

- Nothing blocking. All three seam-level cycles (retrieval, embedding, generation) are now done; next cycle is the `answer_query` workflow that orchestrates them end-to-end (embed → retrieve → generate → persist).

### 2026-08-02 Vertical Slice 0001: answer_query Workflow Orchestration

Human direction: continue.

AI contribution:

- Kept this cycle scoped strictly to orchestration logic, per the plan's explicit test-style call-out ("repository and both providers injected as stubs/test doubles") and the "no anticipating later cycles" TDD discipline: `QueryRepository` is defined here only as a `Protocol` (the persistence contract), with no Postgres-backed implementation yet — that's deferred to the API-endpoint cycle (6), which is the first point anything actually needs a real database write. Building it now would have been implementation work the current cycle doesn't call for.
- `AnswerQueryWorkflow.answer_query` composes the three already-built seams (embed → `find_similar_passages` → `generate_answer`) and derives `grounding_status` from whether any citations came back, rather than trusting the generation provider to report it — keeps the domain invariant (grounded/partial/ungrounded answers have the right citation count) enforced in one place.
- Reused the real `StubEmbeddingProvider` and `StubGenerationProvider` adapters from the previous two cycles in this workflow's test, rather than writing new ad-hoc fakes for them — only `CorpusRepository` and `QueryRepository` needed test doubles, since those don't have a checked-in stub yet.
- Ran red-before-green as with every prior cycle. 5 passed, 2 skipped (the two live provider tests, correctly), `ruff check` clean.

Human judgment still required:

- Nothing blocking. Next cycle is the `POST /queries` API endpoint (dev-authenticated request with valid Workspace Membership returns 200 with Answer + Citation; without valid membership, rejected) — this is the first cycle that needs real Workspace/Membership schema and the Postgres-backed `QueryRepository`, per the deferred-until-needed approach above.

### 2026-08-02 Vertical Slice 0001: POST /queries API Endpoint

Human direction: continue.

AI contribution:

- Added migration `0002`: `users`, `workspaces`, `workspace_memberships` (needed now for the dev-auth precondition, even though they weren't in the slice's minimal Data Shape list, since the slice doc's Preconditions section explicitly calls for a Workspace Membership check), plus `queries`, `answers`, `citations` — following the slice's minimal Query shape from cycle 2/4's precedent (no `created_by_user_id`, even though the full domain model lists it as essential) rather than reopening the already-tested workflow's signature from the previous cycle.
- Modeled dev-auth and the membership check on HiveSight core-api's own pattern (read `main.py`/`dev_store.py` directly rather than inventing a new convention): header-based dev user resolution, a membership check before any workflow work happens, rejecting with 403 before either the corpus or generation seam is touched.
- Wired dependency injection (`dependencies.py`) so `EmbeddingProvider`/`GenerationProvider` fall back to their stub adapters whenever `VOYAGE_API_KEY`/`ANTHROPIC_API_KEY` aren't set — meaning the integration test needed no explicit stub override, only a real-Postgres override for the DB connection (`CorpusRepository`/`QueryRepository` are exercised for real, per the plan's "not mocked" guidance for those two; the provider seams are stubbed by environment absence, not by test-time patching).
- Ran red-before-green for both the happy path (valid membership → 200, grounded answer, correct citation) and the rejection path (no membership → 403) in one integration test file, matching the plan's Test Seams description for this cycle.
- 7 passed, 2 skipped (the two live provider tests, correctly), `ruff check` clean after one auto-fixed import-sort nit.

Human judgment still required:

- Nothing blocking. Backend is now feature-complete for Slice 0001's Advisor Service; remaining plan steps (7–9) are the web API client seam, the web UI workflow, and the end-to-end acceptance test, plus the checked-in seed script (`scripts/seed_slice_0001.py`) for the hand-seeded Passage per the Slice 0001 Test And Seed Approach decision.

### 2026-08-02 Vertical Slice 0001: End-To-End Demo (Web UI + Seed Script)

Human direction: carry on until there's something demo-able from a frontend perspective.

AI contribution:

- Wrote `scripts/seed_slice_0001.py`: idempotent (`ON CONFLICT ... DO NOTHING` throughout), fixed dev IDs so the frontend can hardcode them without a registration flow, and a real Voyage embedding call for the seeded Passage rather than a fabricated vector — matching both the plan's Seed Script section and the Slice 0001 Test And Seed Approach decision.
- Scaffolded `apps/web` (Vite + React + TS, modelled on HiveSight's `apps/web` conventions — same `devAuthHeaders`/`ensureOk`/manual runtime-validation parsing pattern in the API client, just scoped to this one endpoint) with `QueryForm`, `AnswerView`, and a thin `App` wiring them to the real `/queries` endpoint.
- **Caught a real secret-handling mistake before it became one**: the human pasted real Voyage/Anthropic API keys into `.env.example`, which is a tracked, non-gitignored file — checked `git status`/`git log` first (confirmed the file had never been committed, so nothing had actually leaked), then moved the keys to the already-gitignored `services/advisor-api/.env` and restored `.env.example` to placeholders. Edited that file with `sed` rather than reading it, specifically to avoid pulling the raw key values into this transcript.
- Hit two port conflicts against the human's already-running HiveSight dev servers (Postgres on 5432 in the previous cycle; API on 8000 and web on 5173 here) — ran this project's servers on 5433/8010/5183 instead each time rather than touching the other project's processes, and the human confirmed 8000/5173 are reserved for HiveSight specifically.
- Verified the full stack live in the browser pane (not Playwright — that's the separate, still-pending automated acceptance test from the plan): typed a real question, got a genuine Claude-generated answer grounded in the seeded passage, correctly citing it.

Human judgment still required:

- The manual demo pass is not a substitute for the plan's remaining automated coverage: `advisorApiClient.submitQuery` unit test (mocked fetch), a component-level test for the `QueryForm`/`AnswerView` workflow, and the `pytest-bdd` end-to-end acceptance test matching HiveSight's `test_vertical_slice_NNNN_bdd.py` convention. None of those exist yet.

### 2026-08-02 Vertical Slice 0001: Remaining Test Coverage (Client Unit Test, Web UI E2E)

Human direction: build both remaining pieces — the client unit test, then the end-to-end acceptance test — parking lot item PARK-0001 (Playwright + Gherkin) resolved as part of this.

AI contribution:

- Added `vitest` to `apps/web` and wrote `advisorApiClient.submitQuery.test.ts` covering both the success path (correct request shape, parsed `Answer`) and the error path (non-ok response surfaces the server's `detail` message). Caught and fixed a real conflict: Vitest's default file discovery picked up Playwright-BDD's generated spec file (`.features-gen/**`) and failed to collect it (different `test` APIs) — scoped Vitest to `src/**/*.test.ts` via `vitest/config`'s `defineConfig` to fix it, rather than the fragile alternative of excluding the generated directory by name.
- **Deviated from the plan's literal text on purpose**: the plan named `pytest-bdd` (matching HiveSight's Python API-level acceptance convention) for the end-to-end test, but the human's actual direction (parking lot PARK-0001) was Gherkin at the *web UI* layer specifically, driven by Playwright — a different layer than what HiveSight's `pytest-bdd` convention covers (HiveSight's own UI acceptance is plain Playwright specs, no Gherkin at all). Followed the human's explicit instruction over the plan's literal wording once the two diverged.
- Chose `playwright-bdd` as the Gherkin-to-Playwright bridge over hand-wiring `@cucumber/cucumber` directly against Playwright, since it integrates with the existing `@playwright/test` config and runner rather than requiring a second test runner alongside it — lower integration surface for a single-developer project to maintain.
- Wrote the acceptance scenario directly from the slice doc's own User Path section (`vertical_slice_0001_grounded_query_answer.feature`), so the executable spec and the design doc describe the same journey in the same order.
- Built a `globalSetup` hook that seeds a dedicated `_test`-suffixed Postgres database with the stub embedding adapter before the run, and pinned the API server under test to that database with both provider API keys explicitly cleared — so the acceptance run is deterministic and cannot incur real Voyage/Claude spend regardless of what's in the developer's own `.env`. Ran on its own port pair (8020/5193), avoiding both this project's dev ports (8010/5183) and HiveSight's (8000/5173).
- Hit one real tooling gap: `playwright-bdd` 9.x's `defineBddConfig` did not auto-generate test files on a plain `playwright test` run in this setup; added an explicit `bddgen` step ahead of it in the `test:acceptance` script rather than relying on undocumented auto-generation behavior.
- Full suite green: Python (7 passed, 2 skipped — live provider tests correctly skip), Vitest (2 passed), Playwright acceptance (1 passed, ~5s).

Human judgment still required:

- All of Slice 0001's planned automated coverage now exists and passes. Nothing blocking for this slice; next scope decision is what to build for Slice 0002 (a second jurisdiction, per the slice doc's own stated next step for actually proving FR-003's non-blending requirement).

### 2026-08-02 Vertical Slice 0002: Scoping (Second Jurisdiction, Non-Blending Proof)

Human direction: scope Slice 0002.

AI contribution:

- Followed `sdlc-delivery-vertical-slice-planning`'s process rather than jumping straight to an implementation plan: read the decision log, `CONTEXT.md`, domain model, and Slice 0001's own doc first.
- **Caught a factual error while gathering context, not incidentally**: `requirements/decision-log.md`'s V1 Jurisdiction Scope decision explicitly says HBHC is the *US* source and APHA BeeBase is the *UK* source, but Slice 0001's seed script had labelled the UK Corpus Document's source as "Healthy Bees Healthy Colonies (HBHC) guide" — backwards. Folded the correction into this slice's scope (and its own acceptance criterion) rather than filing it separately, since Slice 0002 is precisely the moment a genuine HBHC-sourced US document is added, which is when leaving the mislabel in place would go from merely inconsistent to actively misleading.
- Checked the existing code before writing the slice, not just the docs: confirmed `CorpusRepository.find_similar_passages` already scopes retrieval by `jurisdiction_id` in its `WHERE` clause. This means FR-003's non-blending guarantee is already structurally enforced by construction — Slice 0002 doesn't need new prevention logic, only real second-Jurisdiction data and a test that actually exercises the filter with two Jurisdictions present (Slice 0001 only ever seeded one, so this path has never really been tested). This materially thinned the slice versus treating it as "build jurisdiction isolation."
- Chose US Passage content deliberately distinct from the UK Passage's oxalic-acid-vaporisation focus (HBHC's registered-miticide rotation approach) rather than a reworded duplicate, so a real answer difference is demonstrable between Jurisdictions, not just a different source label on similar text.
- Wrote `architecture/vertical-slice-0002-second-jurisdiction-and-non-blending-proof.md` per the skill's required structure. No open questions — the slice's shape follows directly from decisions already confirmed during Slice 0001 planning, so no fresh grilling was needed.

Human judgment still required:

- Approve the slice doc (or adjust) before implementation planning/TDD begins, per the vertical-slice-planning skill's step 10.

### 2026-08-02 Vertical Slice 0002: Implementation

Human direction: approved; go ahead and implement.

AI contribution:

- Restructured `scripts/seed_slice_0001.py` from one hardcoded passage to a small `SeedJurisdiction` list, iterated once per jurisdiction, rather than duplicating the insert logic for a second jurisdiction inline — the script now naturally extends to a third jurisdiction (EU, when that's eventually unblocked) without another restructure.
- Corrected the UK Corpus Document's `source` from the mislabelled "HBHC" to "APHA BeeBase" (with `Open Government Licence` as its licence, reflecting it being a UK government source, distinct from HBHC's `CC BY-NC-ND`) — and changed the seed script's `ON CONFLICT` handling on `corpus_documents`/`passages` from `DO NOTHING` to `DO UPDATE`, since a "rerunnable seed script" that can't actually correct a previously-seeded field isn't rerunnable in the way the decision log intended.
- Wrote the new `CorpusRepository` test specifically to make the jurisdiction filter's absence would-be-detectable: seeded a second jurisdiction's passage as the *closer* vector match (distance 0) to the query embedding, so if the `WHERE jurisdiction_id = ...` clause were ever removed or broken, the test would fail by returning the wrong passage — not simply by returning zero results.
- Kept Slice 0001's original feature file untouched and added a new `vertical_slice_0002_second_jurisdiction_non_blending.feature` rather than editing the first — each slice's executable spec still matches exactly what that slice proved, and the new one uses a Scenario Outline over both jurisdictions so the non-blending proof reads as one intentional check, not two copy-pasted scenarios.
- Verified live in the browser after re-seeding the real dev database (real Voyage embeddings, real Claude generation): asking the same underlying question under UK vs. US jurisdiction returns genuinely different, jurisdiction-appropriate guidance (oxalic acid vaporisation vs. alcohol-wash threshold monitoring with product rotation) citing the correct jurisdiction's passage each time — not just structurally correct, but substantively demonstrating why blending would have been actively misleading.
- Full suite green: Python (8 passed, 2 skipped), Vitest (2 passed), Playwright acceptance (3 passed — Slice 0001's original scenario plus both Slice 0002 outline examples).

Human judgment still required:

- Nothing blocking. Slice 0002's acceptance criteria are all met. Next scope decision is open — could be Slice 0003 (a further FR, e.g. source supersession/conflict detection or the no-grounding path) or hardening/ops work on what already exists.

### 2026-08-02 Documentation: Business, Architecture, And Code Diagrams

Human direction: draw a business picture, an architecture picture, and a code picture of what's been built; then roll those and their supporting detail into the appropriate markdown files.

AI contribution:

- Placed each diagram in the doc that already matched its audience rather than creating one dump file: the business diagram went into `requirements/vision.md` (a new "How It Works Today" section, tied to the two slice docs it demonstrates), the architecture diagram into `architecture/system-context.md` as a new "Current Implementation Snapshot" section rather than replacing the original planning diagram — the two are kept side by side with an explicit mapping (Advisor Service = Advisor API, Embedding/Generation Provider = Voyage AI/Claude, Advisor Data Store + Corpus Store = one Postgres database) so the planning artifact's history isn't lost.
- Created `architecture/codebase-design.md` as a new file, modelled directly on HiveSight's own file of the same name and vocabulary (module/interface/seam/adapter/depth), since hive-sight-advisor didn't have an equivalent doc yet and the code-structure diagram needed somewhere durable to live.
- Converted all three from the interactive SVG widgets shown in-chat to Mermaid, matching this repo's existing diagram convention (`system-context.md`, `domain-model-diagram.md` both already use Mermaid) rather than leaving them as one-off chat visuals with no source of truth in the repo.

Human judgment still required:

- None for this documentation pass. Same open scope question as above: what to build for Slice 0003.

### 2026-08-02 Vertical Slice 0003 Scoping: No-Grounding Behaviour (FR-008)

Human direction: check requirements/product spec for open scope before picking a next slice. Reviewed `requirements/requirements.md` directly against what Slices 0001–0002 actually cover (FR-000 through FR-003) rather than relying on memory, confirmed FR-004 through FR-008 and NFR-003 remain genuinely uncovered, and recommended FR-008 (no-grounding behaviour) as the next slice — it's the one gap in the core loop already being demoed, versus FR-004–007 which are additive capabilities on a loop that already works. Human agreed.

AI contribution:

- Drafted a mechanism (not yet a formal slice doc) surfacing four real open questions, then ran a one-question-at-a-time grilling session per `productivity-grilling` rather than presenting all four at once — each with a stated recommendation, each confirmed individually before moving to the next.
- Caught the real gap driving this slice while drafting: `CorpusRepository.find_similar_passages` today always returns the closest Passage regardless of how far away it actually is — there is no threshold, so an entirely off-topic question would currently still be silently treated as grounded. The fix is exposing the similarity distance from retrieval and classifying against it, not building new prevention logic elsewhere.
- Grilled and logged one combined decision-log entry (FR-008 Grounding Classification Mechanism) covering all four resolutions: deterministic distance threshold over model judgment (testability, no live-call dependency); skip the generation call entirely for `ungrounded` (nothing to ground a nuanced answer in, avoids unnecessary spend); pick provisional threshold values now rather than waiting for a calibration dataset that doesn't exist yet (the corpus only has two Passages); and include `partial`, not just a two-state split, since the domain model already carries that shape and the same mechanism produces it for free.
- Wrote `architecture/vertical-slice-0003-no-grounding-behaviour.md` per the vertical-slice-planning skill's structure, with all open questions already resolved — nothing left open in the doc itself.

Human judgment still required:

- Approve the slice doc (or adjust) before implementation/TDD begins.

### 2026-08-03 Vertical Slice 0003 Implementation: No-Grounding Behaviour (FR-008)

Human direction: "please do" — implement the slice as scoped and grilled.

AI contribution:

- Backend, TDD throughout: calibrated real thresholds (0.35/0.55) via a handful of live Voyage AI calls against the seeded UK Passage; redesigned `StubEmbeddingProvider` from a meaningless pure-hash scheme to a word-hashing bag-of-words embedding so textual overlap correlates with cosine similarity, with a test proving that property via 3 related/3 unrelated text pairs and a strict max/min ordering assertion (a single-pair version passed by chance against the old broken implementation, so it was redesigned to be a reliable red before going green); added `distance: float` to `CorpusRepository.Passage`; implemented grounded/partial/ungrounded classification in `AnswerQueryWorkflow`, skipping the generation call entirely when ungrounded.
- UI: `AnswerView` now renders a distinct banner and border colour per grounding state, not just a text label change.
- Extended the Playwright + Gherkin suite with two new scenarios (partial, ungrounded) using UK-jurisdiction query text.
- Caught a real regression while doing so: the existing "grounded" Playwright scenarios started failing, because the stub embedding's word-hash distances sit on a completely different scale than the real-Voyage-calibrated thresholds — even a query built almost entirely from the Passage's own vocabulary only reached ~0.43 distance, and the existing scenario's query scored 0.76. Surfaced this to the user with three options before proceeding; user deferred the choice ("do whatever you think best"). Resolved by making the thresholds Settings-driven (env-configurable), with the Playwright config overriding them to stub-calibrated values (0.5/0.8) for its own spawned API process only — production keeps the real calibrated defaults. Logged as its own decision-log entry since it changes how the thresholds are wired, not just their values.
- Also fixed an unrelated but adjacent bug found while touching `.env.example` for the above: it still documented HiveSight's reserved ports (5173/8000) for `ADVISOR_API_ALLOWED_ORIGINS`/`VITE_ADVISOR_API_URL`, contradicting the explicit port-conflict-avoidance decision from earlier in the project (this project owns 8010/5183). The real, gitignored `.env` already had the correct port — only the example file was stale.
- Verified: full Python suite (13 passed, 2 skipped, `ruff` clean), Vitest (2 passed), Playwright + Gherkin (5 passed, including the 2 new scenarios), and a live manual pass in the browser against the real Voyage/Claude backend confirming all three grounding states render distinctly (ungrounded and partial both visually confirmed with real API responses; grounded already confirmed in Slices 0001–0002).

Human judgment still required:

- None outstanding for this slice — all acceptance criteria met. Next step is the same open-scope question as before: FR-004 through FR-007 and NFR-003 remain uncovered by any slice.

### 2026-08-03 Vertical Slice 0004 Scoping: Source Supersession And Provenance Display (FR-005 + NFR-003)

Human direction: "what next" after Slice 0003. Recommended pairing FR-005 (source supersession) with NFR-003 (provenance/licence metadata) as the smallest remaining gap, rather than FR-007 (bigger — needs a new write path) or FR-004/FR-006 (bigger — need multiple competing corpus passages, not just metadata). User agreed and asked to scope it.

AI contribution:

- Checked the actual schema and domain model before drafting rather than assuming a blank slate: `corpus_documents` already has `source`, `licence_terms`, `status`, and `superseded_by_corpus_document_id` from Slice 0001's migration, populated with real values by the seed script but never surfaced past the repository layer — and the UI today renders a citation as a raw passage UUID, not even a document title. Also found the domain model calls for two fields never actually built into the schema: "source url or reference" and "retrieved/version date."
- Drafted a mechanism surfacing six real open questions, then ran the same one-question-at-a-time grilling pattern as Slice 0003 — each with a stated recommendation, each confirmed individually before moving to the next.
- Key resolutions: retrieval still surfaces and cites superseded documents (excluding them would make the "flag" behaviour in FR-005's own wording unobservable); the superseded signal lives on the Citation, not as a fourth `grounding_status` value, keeping "well-matched" and "current" as independent dimensions; NFR-003 applies unconditionally to every citation, not just superseded ones; `created_at` is treated as satisfying the domain model's "retrieved/version date" for v1 (deferred, not built) while a new `source_url` column is added now (cheap, and materially strengthens NFR-003's real licence-attribution intent) — two schema gaps judged on different cost/value terms rather than both deferred or both built by default.
- Wrote `architecture/vertical-slice-0004-source-supersession-and-provenance.md` and logged one combined decision-log entry covering all six resolutions.

Human judgment still required:

- Approve the slice doc (or adjust) before implementation/TDD begins.

### 2026-08-03 Vertical Slice 0004 Implementation: Source Supersession And Provenance Display (FR-005 + NFR-003)

Human direction: "go for it" — implement the slice as scoped and grilled.

AI contribution:

- Caught and corrected a drafting error before implementation started: the slice doc claimed the superseded case would "tell the generation provider to hedge, mirroring `partial`," but checking the actual Slice 0003 code showed `partial` never touches the generation prompt — Claude just naturally hedges when the passage is a poor match. Simplified the mechanism to pure Citation-level metadata with no generation-provider changes, and corrected the slice doc and decision log to match before writing any code.
- TDD throughout, backend first: added a `source_url` migration; extended `CorpusRepository.find_similar_passages` to join through each Passage's parent Corpus Document (title, source, source URL, licence terms, status, superseding document's title via a self-join); extended `AnswerQueryWorkflow`'s `Citation` to carry that provenance on every citation unconditionally and flag `is_superseded` when the source document's status is `superseded`.
- Seed script: added real source URLs for both existing documents, and seeded one new, deliberately outdated UK document (an old Apistan/fluvalinate-strip guide, since superseded by widespread resistance) marked `superseded_by_corpus_document_id` pointing at the current UK guide — giving the slice something real to demonstrate against.
- UI: citation rendering upgraded from a raw passage UUID to a real attribution block (title, clickable source link, licence terms), with a distinct amber warning banner when a citation's source is superseded.
- Extending the Playwright + Gherkin suite surfaced an expected knock-on effect: the old step definitions asserted a citation `.toContainText` the passage's raw UUID, which no longer appears anywhere in the DOM now that citations render real attribution instead. Updated those step definitions (Slices 0001 and 0002) to check for the document's title instead — a more meaningful assertion than the UUID ever was, not a workaround.
- Verified: full Python suite (17 passed, 2 skipped, `ruff` clean), Vitest (2 passed), `tsc --noEmit` clean, Playwright + Gherkin (7 passed, including the 2 new scenarios), and a live manual pass in the browser against the real Voyage/Claude backend confirming the superseded-source warning, clickable source link, and licence terms all render correctly.

Human judgment still required:

- None outstanding for this slice — all acceptance criteria met. FR-004, FR-006, and FR-007 remain the only uncovered functional requirements.

### 2026-08-03 Vertical Slice 0005 Scoping: User Corrections (FR-007)

Human direction: "on with the next" after Slice 0004. Recommended FR-007 (user corrections) over FR-006 (source conflict detection, needs multi-passage retrieval plus a mechanism to record which documents conflict) and FR-004 (treatment trade-off comparison, needs a richer corpus) — FR-007 is the most self-contained: a new write path against an entity the domain model already fully specifies, with no retrieval-algorithm changes needed. User agreed.

AI contribution:

- Noted the trust-level question (no review gate, straight to `trusted`) was already resolved in an earlier grilling round (Correction Trust Level For V1) — did not re-litigate it, only grilled the mechanical/UX questions this slice actually introduces.
- Drafted a mechanism surfacing four open questions, then ran the same one-question-at-a-time grilling pattern as Slices 0003–0004.
- Key resolutions: the flag control is available on every Answer including `ungrounded` (the grounding thresholds are provisional, so disagreement with an ungrounded classification is itself valuable evidence); notes are required, not optional; repeat Corrections on the same Answer are allowed, not one-shot; no reason taxonomy for v1, free-text only.
- Wrote `architecture/vertical-slice-0005-user-corrections.md` and logged one combined decision-log entry covering all four resolutions.

Human judgment still required:

- Approve the slice doc (or adjust) before implementation/TDD begins.

### 2026-08-03 Vertical Slice 0005 Implementation: User Corrections (FR-007)

Human direction: "go for it" — implement the slice as scoped and grilled.

AI contribution:

- TDD throughout: new `corrections` migration; `CorrectionRepository` (`save`, `answer_belongs_to_workspace`, the latter validating an Answer's parent Query belongs to the claimed Workspace before allowing a Correction against it); new `POST /corrections` endpoint reusing the existing `has_active_membership` check from `QueryRepository` rather than duplicating it, with Pydantic's `Field(min_length=1)` enforcing required notes as a free built-in 422 rather than custom validation code.
- UI: `AnswerView` gained a self-contained "Flag as wrong" control (button → notes form → submit → acknowledgment → "Flag again"), managing its own local state and calling the API client directly, since App.tsx has no reason to react to a Correction's outcome — kept the page-level state machine untouched.
- Extended the Playwright + Gherkin suite with 2 new scenarios covering both a grounded and an ungrounded Answer being flagged, proving the control and full round-trip work regardless of grounding status per the grilled decision.
- Verified: full Python suite (27 passed, 2 skipped, `ruff` clean), Vitest (4 passed), `tsc --noEmit` clean, Playwright + Gherkin (9 passed, including the 2 new scenarios), a live manual pass in the browser against the real backend, and a direct database check confirming the Correction row persisted with `status = 'trusted'` and the submitted notes intact.

Human judgment still required:

- None outstanding for this slice — all acceptance criteria met. FR-004 and FR-006 remain the only uncovered functional requirements.

### 2026-08-03 Roadmap Document And CI Pipeline

Human direction: wanted a standing document listing candidate future slices broken into business/technical categories, since none existed. After reviewing it, asked "what is next" again; recommended a CI pipeline over touching FR-004/FR-006 directly, since both remaining functional requirements need genuine content-sourcing work (real, accurately-cited treatment-option documents) first, which is a different kind of task from engineering work and shouldn't be rushed into. User agreed.

AI contribution:

- Wrote `requirements/roadmap.md`: Business and Technical sections, every item cross-checked against the actual repo state before being listed (e.g. confirmed no `.github/workflows` existed before citing that as a gap, verified decision-log entry titles cited exactly rather than paraphrased) rather than assuming or fabricating gaps.
- Implemented `.github/workflows/ci.yml`: three parallel jobs — `backend` (pytest + ruff against a `pgvector/pgvector:pg16` service container, mirroring `docker-compose.yml` exactly so no `DATABASE_URL` override is needed), `web` (tsc + Vitest, no database needed), and `acceptance` (builds the `.venv-advisor-api` venv at the exact relative path `playwright.config.ts` already hardcodes, installs Playwright's Chromium browser only, runs the full Gherkin suite, uploads the HTML report as an artifact on any outcome). No GitHub secrets are required anywhere in the pipeline, since every test path already runs on stub providers.
- Added a `test:web` root script (`pnpm --filter hive-sight-advisor-web test`) to match the existing `check:web`/`build:web`/`dev:web` naming convention, used by both the new CI job and available locally.
- Verified locally before considering it done: `pnpm install --frozen-lockfile` (matches CI's install step), the new `check:web`/`test:web` scripts, and validated the workflow YAML actually parses with the expected job structure (no live GitHub Actions run possible from here, since the workflow only executes once pushed).
- User asked mid-task whether this required git; confirmed it didn't — the workflow file itself is authored the same way as every other slice, and per the standing git-hands-off preference, committing and pushing (which is the only way to actually see it run) is the user's action, not something performed here.

Human judgment still required:

- Push this to GitHub to see the pipeline actually execute for the first time — nothing here can be verified against real GitHub Actions infrastructure from this environment.
- Decide next: FR-004/FR-006 (needs real source content first) vs. another Technical-category item from the roadmap.

### 2026-08-03 CI Pipeline: First Real Run Caught A Genuine Bug

Human direction: git policy was clarified (see memory — the "hands-off" rule had always meant confirm-each-action, not never-touch-git; a stale one-line summary in the memory index had drifted to say otherwise, and was corrected). User then asked to commit and push the roadmap/CI work directly.

AI contribution:

- After pushing, checked the actual GitHub Actions run via `gh run list`/`gh run view` rather than assuming success — the `acceptance` job failed at "Install Playwright browsers" with `ERROR packages field missing or empty`.
- Root-caused it: `pnpm-workspace.yaml`'s `allowBuilds` field was only introduced in pnpm 10.26, but the CI workflow had pinned `pnpm/action-setup` to version 9 (mistakenly inferred from the lockfile's `lockfileVersion: '9.0'`, which is actually a lockfile *format* version compatible with much newer pnpm CLI releases, not the CLI version itself — a real reasoning error worth naming explicitly). pnpm 9 can't parse `allowBuilds` and fails ambiguously rather than with a clear "unknown field" error.
- Fixed by pinning to pnpm 11, matching what's actually used locally. Verified by watching the corrected run go green end-to-end (`backend`, `web`, and `acceptance` all passed) via `gh run view`, not just by re-reading the YAML.
- This is a concrete demonstration of why "I can't verify it without pushing" (stated when this pipeline was first built) was accurate — a config bug that passed every local check (YAML parsing, `pnpm install --frozen-lockfile`, the scripts running fine on the developer's own already-provisioned pnpm 11 install) only surfaced once real GitHub Actions infrastructure with a freshly pinned pnpm 9 actually ran it.

Human judgment still required:

- None — CI is green. Same open decision as above: FR-004/FR-006 vs. another Technical-category roadmap item.

### 2026-08-03 UK Corpus Growth: Real Treatment-Option Documents For FR-004

Human direction: "Let's pick up FR-005 source content for FR-004/FR-006" — pick up the roadmap's corpus-growth item to unblock the two remaining functional requirements. Asked first how to source it, since these passages become grounding truth the system cites as authoritative: user chose researching real published guidance (not fabricating content) over supplying source material directly, and chose the UK jurisdiction to start.

AI contribution:

- Researched real, currently-authorised UK Varroa treatments via WebSearch/WebFetch rather than inventing plausible-sounding content: Apivar (amitraz, Thorne retailer product page) and Apiguard (thymol, Vita Bee Health's own manufacturer FAQ), cross-checking product-label facts (temperature constraints, organic-certification compatibility, honey-super timing) against multiple sources before writing anything.
- Found the two products give genuinely different, real trade-off attributes alongside the corpus's existing oxalic-acid document — no temperature constraint but not organic-certifiable (Apivar) vs. needs warm weather but is organic-certifiable (Apiguard) vs. typically broodless-season timing (the existing oxalic acid document) — real material for a future FR-004 comparison slice, not contrived.
- Flagged before writing anything that Apivar/Apiguard's sources (a retailer page, a manufacturer FAQ) don't carry an open licence like the existing OGL/CC-BY-NC-ND documents, so their `licence_terms` are honestly framed as "all rights reserved (retailer/manufacturer product literature)" rather than borrowing the existing documents' framing. Confirmed with the user before seeding.
- Also flagged and deliberately scoped out FR-006: couldn't find a real, clean example of two UK authoritative sources materially disagreeing (manufacturers/regulators don't tend to publish contradictions), so didn't force one into the corpus — left as a separate, harder future research task rather than fabricating a disagreement to satisfy the requirement.
- Implementation was pure content/data work, not new behaviour: added the two documents to `scripts/seed_slice_0001.py`'s existing `AdditionalDocument` pattern (mirroring the `SupersededDocument` pattern from Slice 0004) — no backend code changes were needed, since multi-document-per-jurisdiction retrieval already worked correctly from Slice 0004 onward.
- Hit the known Voyage AI free-tier rate limit (documented in the roadmap) re-seeding the real dev database with 5 embedding calls in one run; worked around it with a one-off paced-embedding wrapper script in the scratchpad, not a permanent change to the seed script or `VoyageEmbeddingProvider`.
- Verified: full Python suite and Playwright/Gherkin suite both still pass unchanged (9/9 acceptance scenarios, no regressions from the richer corpus), and live queries against the real backend confirmed both new documents retrieve correctly with accurate citations, while a generic autumn-treatment query still correctly retrieves the original oxalic-acid document rather than being confused by the new options.

Human judgment still required:

- FR-004 itself (the actual trade-off-comparison feature) is still unbuilt — this was corpus preparation, not the feature. Needs its own scoping/grilling pass.
- FR-006 still has no real source content; US jurisdiction still has only one document.

### 2026-08-03 Corpus Management Question: Two Distinct Future Capabilities Identified

Human direction: asked how the corpus (public-domain/licensed documents) should be managed and curated going forward — could a user point the system at a new document, or remove one, and does this need a full admin layer.

AI contribution:

- Recognized the question actually spans two capabilities with very different implications rather than answering as if it were one: internal Corpus Curator tooling (an already-trusted operator, no moderation question) versus an end-user document-suggestion feature (affects every user's answers in that jurisdiction, so raises a genuine trust/review question this project hasn't answered — unlike a Correction, which only affects the submitter's own evaluation evidence). Asked the user to confirm scope rather than assuming either. User chose: both, but scoped as two separate future items.
- Pointed out the internal-tooling half isn't actually a gap needing urgent attention — it's the deliberate outcome of prior decisions (Ingestion Trigger, Source Supersession And Conflict Detection) that chose manual, script-based curation over building tooling ahead of the pain.
- Added both as new candidate items in `requirements/roadmap.md`: "Corpus contribution and curation" (Business — end-user suggestion, needs a submission-plus-review-gate trust model, its own future grilling session) and "Corpus management tooling" (Technical — an internal CLI/admin script wrapping the existing repository calls, no trust model needed).

Human judgment still required:

- Neither item is scoped yet — both are roadmap candidates only. Decide which (if either) to pick up next, or continue with FR-004/FR-006.

### 2026-08-03 Vertical Slice 0006 Scoping: Corpus Curator CLI Tooling With AI-Assisted Review

Human direction: "The internal corpus management one looks an interesting one to start with." Mid-scoping, before hearing the drafted questions, the user raised a genuinely good addition: since they lack domain expertise to judge what makes a good corpus document, could the system itself review a candidate document and give guidance before it's added.

AI contribution:

- Recognized the review idea connects directly to an existing decision (Source Supersession And Conflict Detection: manual, Curator-led judgement at ingestion time) rather than treating it as an unrelated new feature — framed it as assisting that existing manual judgement, not automating past it.
- Folded the review idea into the same grilling session as the tool's own design, asking about it first since the user raised it first: what the review checks (relevance/overlap, not factual accuracy — an LLM shouldn't be a false authority on specialized veterinary/apiculture facts), whether it's advisory or blocking (advisory only, same reasoning as Correction Trust Level For V1), and whether it compares against existing corpus content (yes, reusing existing retrieval infrastructure — also real groundwork toward FR-006, which had no source material to work with as of the last corpus-growth pass).
- Then returned to the four originally-planned questions about the tool's own shape: CLI script over HTTP admin endpoints (avoids an access-control model that doesn't exist), persisting additions to a source-controlled file rather than the live database alone (protects the reproducibility property every other part of this project already has), a separate YAML file over rewriting Python source (avoids fragile programmatic source-code editing), and add/retire-only v1 scope (matches exactly what was asked for).
- Wrote `architecture/vertical-slice-0006-corpus-curator-cli-tooling.md` and logged one combined decision-log entry covering all seven resolutions.

Human judgment still required:

- Approve the slice doc (or adjust) before implementation/TDD begins.

### 2026-08-03 Vertical Slice 0006 Implementation: Corpus Curator CLI Tooling With AI-Assisted Review

Human direction: "Go for it" — implement the slice as scoped and grilled.

AI contribution:

- Refined one placement decision beyond what was grilled (not itself a product question): put the CLI's core logic inside the installed package (`hive_sight_advisor_api/corpus_admin.py`) rather than `scripts/`, matching `db.py`'s existing precedent for argparse-based operational tooling and making it importable by pytest with no path workarounds — `scripts/` stays reserved for data/seeding scripts (`seed_slice_0001.py`) and the data file itself.
- TDD throughout: `CorpusReviewProvider` protocol + `StubCorpusReviewProvider` + `ClaudeCorpusReviewProvider` (mirroring the existing `EmbeddingProvider`/`GenerationProvider` two-adapter pattern); `corpus_admin.py`'s `prepare_candidate`/`commit_candidate`/`retire_document`/`apply_curator_documents` written as plain testable functions against a real Postgres test database, with the interactive/argparse concerns kept in a thin `main()` wrapper.
- Extended `seed_slice_0001.py` to load and apply `scripts/curator_added_documents.yaml` after seeding its existing hardcoded documents, so retiring a document works identically whether it originated from the Python baseline or a prior CLI addition.
- Verified: full Python suite (38 passed, 3 skipped, `ruff` clean — the 3 skips are the pre-existing live-provider contract tests, correctly including the new Claude review contract test), Playwright/Gherkin (9/9, no regressions from the empty data file being wired in).
- Ran the real tool against the live dev database to prove it end-to-end, adding a genuine new US document (Formic Pro, formic acid, EPA-registered) researched the same way as the earlier UK corpus-growth pass. The AI review caught something genuinely useful unprompted: it flagged that the candidate's "supers don't need to be removed" claim sits in tension with the existing US passage's blanket "follow the label for honey super restrictions" framing — not a contradiction, but worth a curator's eye — while explicitly declining to judge the temperature range, dosing regimen, or organic-certification claims, deferring those to the curator as out of its remit. This is exactly the advisory shape that was designed.
- Verified reproducibility directly, not just by inspection: ran a full `reset-test` (drop schema, reapply migrations) and re-seed, then confirmed via direct SQL query that the curator-added Formic Pro document reproduced correctly — the property this whole design (source-controlled YAML over live-database-only) exists to protect.

Human judgment still required:

- None outstanding for this slice — all acceptance criteria met.
- `curator_added_documents.yaml` now has one real, live-verified entry (Formic Pro) rather than being an empty template — this is genuine corpus content, not test fixture data, and should be treated the same as the other UK/US treatment documents added earlier.
- Update/mark-superseded via the CLI tool remain deferred, per the grilled v1 scope — still done by hand-editing `seed_slice_0001.py`'s dataclasses.

### 2026-08-03 Vertical Slice 0007 Scoping: Treatment Trade-Off Comparison (FR-004)

Human direction: "Yes please" — scope FR-004 next, per the recommendation that it was the only remaining core-loop requirement with real content already in place (the UK/US corpus growth from earlier slices).

AI contribution:

- Drafted a mechanism surfacing five open questions, then ran the same one-question-at-a-time grilling pattern as prior slices.
- Key resolutions: trade-off attributes stay as prose within Passage text, not structured columns (already proven to work from a live query); retrieval always widens to several closest Passages for every Query rather than detecting "comparison-seeking" questions specially (avoids a fragile intent classifier and a two-code-path architecture); a small fixed retrieval width of 5 (not "all Passages in the jurisdiction"); `grounding_status` stays independent of comparison, based purely on the single closest Passage's distance; no new UI structure, since the existing citations list already supports multiple entries.
- Recognized this scopes out unusually small compared to prior slices: no schema change, no new UI code, no new seed data — mostly a retrieval-width constant and a prompt change, since the corpus content and citation-list UI needed for this were already built by Slices 0002 and 0004–0006.
- Wrote `architecture/vertical-slice-0007-treatment-trade-off-comparison.md` and logged one combined decision-log entry covering all five resolutions.

Human judgment still required:

- Approve the slice doc (or adjust) before implementation/TDD begins.

### 2026-08-03 Vertical Slice 0007 Implementation: Treatment Trade-Off Comparison (FR-004)

Human direction: "Go for it" — implement the slice as scoped and grilled.

AI contribution:

- TDD throughout, and genuinely small as scoped: raised `AnswerQueryWorkflow`'s retrieval limit from 1 to a named `MAX_RETRIEVED_PASSAGES = 5` constant, with new unit tests proving multiple Passages get retrieved and passed to generation while `grounding_status` stays keyed to the closest Passage only, regardless of how many others are also in play.
- Extended `ClaudeGenerationProvider`'s system prompt with explicit compare-when-relevant instructions (temperature, organic-certification, treatment duration), while also explicitly telling it not to force a comparison when only one Passage is actually relevant — added a new live contract test proving this with two genuinely different real UK treatment Passages (Apivar/Apiguard), run for real (not just left to the skip path) to confirm it actually passes, not just that it's plausible.
- Verified: full Python suite (40 passed, 4 skipped — one more skip than before, the new live comparison contract test, which was then also run for real with the API key and passed), ruff clean, Playwright/Gherkin (10/10, no regressions), and — importantly — a live query against the real dev backend and browser that produced a genuine, well-organized comparison across Apiguard and Apivar (correctly calling out the temperature-vs-organic-certification-vs-duration trade-off exactly as FR-004 describes), while also naturally surfacing that the older Apistan guidance is superseded, an unplanned but correct interaction with Slice 0004's existing supersession flagging.
- This is the smallest slice of the whole project so far in terms of new code — the corpus content (Slice 0002 growth, Slice 0006's Formic Pro addition) and the citations-list UI (Slices 0004–0005) needed for this to work end-to-end were already built by the time this slice started, exactly as anticipated when it was scoped.

Human judgment still required:

- None outstanding for this slice — all acceptance criteria met, verified against both stub and real providers. FR-006 (source conflict detection) remains the only uncovered functional requirement, still blocked on finding or surfacing a genuine source disagreement.

### 2026-08-03 Test Coverage Measurement, And A New Requirements-Traceability Discipline

Human direction: asked for a measure of code coverage across test levels. After seeing the numbers, explained the real reason behind the question — the user does not read code on this project (or the sibling HiveSight project) and relies entirely on tests to know the system behaves correctly, including after future refactors. Asked how to structure testing so that requirement holds solidly, then asked for a traceability doc and, if sensible, a new skill.

AI contribution:

- Measured real coverage rather than estimating: added `pytest-cov` (venv-only) and `@vitest/coverage-v8` (a real devDependency, initially installed at the wrong major version — 4.x against a 3.x vitest — caught by the resulting `SyntaxError` and corrected to the matching 3.x release). Backend: 86% statement coverage with live-provider tests run for real, concentrated gaps in the two CLI tools' `main()` entry points (argparse/interactive wiring, correctly low-value to unit-test). Frontend: 92.8% of the one unit-tested module (`advisorApiClient.ts`), 0% of the three React components — not because they're untested, but because they're only exercised through Playwright/Gherkin, a tool Vitest's coverage report can't see into.
- Named the actual distinction the user was reaching for: unit/integration tests are the implementer's safety net (require reading code to interpret, not something this user should need to trust directly); the Gherkin/Playwright acceptance suite is the layer built for exactly this user, since every scenario is already plain English and runs against the real system end-to-end. Pointed out this was already true in practice — every shipped FR already had a corresponding scenario — just never written down as something the user could check without asking.
- Wrote `requirements/traceability.md`: one row per FR/NFR (including FR-000 and the Phase 2/deferred items and the non-functional requirements, not just the "wins"), each honestly marked covered/not-yet-covered/deferred/architectural-property rather than padding the doc to look more complete than it is. Explicitly excludes unit-test file names, on the reasoning that mixing a code-literate list into the one document meant to avoid code-literacy would defeat its purpose.
- Flagged a real, previously-unstated gap while writing it: the acceptance suite proves retrieval/citation/UI *mechanics* via stub providers, not that the real Claude/Voyage integration behaves well — the only current check on real-AI-behaviour is the manual live-browser demos done once per slice, not automated or repeatable. Left this as an open decision rather than silently building a live-test pass without asking.
- Added a new project-local skill, `.claude/skills/requirements-traceability/`, rather than editing the existing shared `sdlc-delivery-acceptance-bdd` skill (personal library, general Gherkin-authoring guidance, not specific to this project's traceability-tracking need, and this project doesn't even use its assumed pytest-bdd runner). Discovered along the way that `.claude/skills` didn't exist in this repo at all — no symlink, despite earlier session context suggesting one was intended — so the new skill is real, committed files, not a symlink to the user's personal library, keeping it reproducible for anyone who clones this repo.
- Housekeeping caught in passing: added `.coverage` and `coverage/` to `.gitignore`, which had never been needed before since no coverage tooling existed.

Human judgment still required:

- Decide whether to keep `@vitest/coverage-v8` as permanent tooling or revert the dependency change, since it was added for this one-off measurement.
- Decide whether the real-provider-behaviour gap (stub-only acceptance suite) needs an automated answer (e.g. an optional live-API scenario pass) or stays a manual-demo-only process.

### 2026-08-03 Resolved The Two Open Points, And The Live Pass Immediately Found A Real Issue

Human direction: "yes" — proceed with both recommendations (revert `@vitest/coverage-v8`; build the on-demand live-API scenario pass).

AI contribution:

- Reverted `@vitest/coverage-v8` cleanly (`pnpm remove`); verified Vitest and `tsc` still pass afterward. `pytest-cov` was already venv-only with no repo diff, so nothing to revert there.
- Built `apps/web/playwright.live.config.ts` and a new `pnpm test:acceptance:live` script: reuses the existing feature files (no duplication), filters to a small subset via `grep` (grounded citation, no-grounding, comparison — the scenarios that meaningfully exercise real AI judgment, not the mostly-mechanical ones like jurisdiction isolation or supersession flagging), runs on distinct ports (8030/5203) against the real dev database with real API keys, and skips the stub-seeding `globalSetup` entirely so it reflects whatever is genuinely in the dev database.
- Ran it for real rather than declaring it done once it existed. First run: 3 of 4 scenarios failed. Rather than assuming a config bug, investigated systematically — reran the full batch again (2 of 4 failed, different scenario passed this time, ruling out a deterministic config error), isolated the grounded-citation scenario alone (passed), then bypassed the browser/API layers entirely and measured the real Voyage distance directly and repeatedly (0.4548, three times, identical) to separate genuine embedding-based drift from LLM-citation sampling noise.
- Found a real, reproducible issue, not a test bug: the grounding thresholds (0.35/0.55) were calibrated when each jurisdiction had one document; the UK jurisdiction now has four (Slices 0002, 0004, 0006). The no-grounding scenario's "unrelated question" example now measures deterministically into `partial` territory against the grown corpus, not the clearly-`ungrounded` result it gave at calibration time — and layered on top, real Claude citation-decision variance means the live suite sometimes still reports `ungrounded` (when Claude happens not to cite) and sometimes `partial` (when it does), on the exact same deterministic distance. Did not attempt to silently patch this (adjust thresholds, reword the scenario) without the user's input — recalibration is a real product decision, not a bug fix, consistent with how the original thresholds were explicitly logged as provisional and revisitable.
- Housekeeping caught in the process: `test-results/` had never been gitignored at all, and `apps/web/playwright-report/index.html` was a tracked file silently churning on every test run since long before this session. Untracked it and added `playwright-report/`, `playwright-report-live/`, and `test-results/` to `.gitignore`.
- Updated `requirements/roadmap.md`'s existing threshold-recalibration item with the concrete evidence (previously a hypothetical "this is provisional" note, now a measured, reproducible finding), and `requirements/traceability.md`'s Real-Provider Behaviour section to document the new live pass and what its first run actually found.

Human judgment still required:

- Decide how to handle the threshold drift: recalibrate 0.35/0.55 against a larger real query set, or accept that some example queries won't cleanly demonstrate their original grounding tier forever as the corpus keeps growing, and choose new example queries per scenario instead.
- The live pass itself is genuinely useful going forward — consider running it after any future corpus-growth or threshold-related change, not just once.

### 2026-08-03 Independent Code Review (Own Pass + Codex), Two Defects Fixed

Human direction: asked for a code review scored on five attributes, "in the same vein" as a review Claude had done on the sibling HiveSight project. Separately, the user had also asked Codex (via ChatGPT) to review this same codebase and shared its findings back for comparison.

AI contribution:

- Ran an independent five-attribute review (Architecture & Design, Security, Test Coverage & Quality, Code Quality & Maintainability, Correctness & Robustness), using a fresh Explore-agent investigation rather than relying on memory of having built the code, since reviewing one's own work carries an inherent bias risk. Verified the two most consequential claims (dead `ADVISOR_API_DEV_USER_HEADER` config, `corpus_admin.py`'s commit-before-yaml-write ordering) directly before including them.
- When the user shared Codex's independent review, verified all five of its findings directly against the actual code rather than accepting them at face value — all five held up. Two were things this review's own pass had missed entirely: retired documents remain fully retrievable (`corpus_repository.py:48` only filters by jurisdiction, no status check), and generated citation ids are trusted via a bare dict lookup (`answer_query.py`, now fixed) with no validation against what was actually retrieved.
- Went a level deeper on the retired-document finding than Codex's own writeup: connected it to Slice 0004's `is_superseded` flag, which checks specifically `document_status == "superseded"` — meaning a `retired` document (exactly what Slice 0006's `retire-document` CLI command produces) renders with *zero* warning, not just "no exclusion." It looks more trustworthy than a superseded document, not less. This was the more actionable finding of the two.
- Fixed both via TDD, deliberately narrow and consistent with prior decisions rather than reopening settled ground: excluded `retired` from retrieval entirely (`corpus_repository.py`, new `AND corpus_documents.status != 'retired'` clause) while leaving `superseded` handling exactly as Slice 0004 decided (retrieve + flag, not exclude) — a real distinction, since `retired` has no named successor to point to the way `superseded` does. Filtered `cited_passage_ids` down to ones present in the retrieved set (`answer_query.py`) rather than adding a new grounding-status branch — the existing "no citations → ungrounded" logic already does the right thing once invalid ids are filtered out first.
- Verified: full Python suite (43 passed, 4 skipped, `ruff` clean) and full Playwright/Gherkin suite (10/10) both green after both fixes, with no regressions to the existing superseded-document behavior.

Human judgment still required:

- Codex's other three findings (generation-version persistence gap, no pgvector ANN index, dev-auth risk) were confirmed accurate but correctly scored as debt/deferred, not "fix now" — no action taken on those yet.
- This review's own additional findings (5x duplicated upsert SQL, no CI type-checking/ESLint, zero retry/timeout on external API adapters, `corpus_admin.py`'s transaction-ordering gaps) remain unaddressed — not yet triaged into the roadmap.

### 2026-08-05 Slice 0008: Agentic Treatment Plan Request (First LangGraph Usage)

Human direction: "Let's start the TDD for Slice 0008" — the scoped, grilled, and scenario-signed-off agentic treatment-plan flow (FR-009's first slice).

AI contribution:

- Ran the TDD loop as seven small vertical slices in dependency order: `HiveSightServiceAuthDep` (shared-secret header, unit-tested directly against the dependency function, no HTTP layer needed) → `proposed_treatments` migration + repository → `TreatmentSuggestionProvider` protocol + stub → the LangGraph graph itself → the completion-confirmation resume path → the `/integrations/hivesight/*` router. Each cycle: red test first, confirmed the failure, then minimal implementation, confirmed green, before moving to the next seam.
- Mid-implementation, reusing `AnswerQueryWorkflow` for the graph's `Recommend` node surfaced a real gap the earlier grilling session hadn't caught: every `Query`/`Answer` row is `Workspace`-scoped (`NOT NULL` foreign key), but this inbound HiveSight call has no Beekeeper/Workspace context at all. Paused implementation and asked the user directly rather than silently choosing — proposed two options (a dedicated internal "system" Workspace row vs. loosening the `NOT NULL` constraint) with a recommendation, got explicit agreement, then proceeded. This is the kind of new/ambiguous seam the TDD skill's own guidance says to confirm rather than invent.
- Treated "the suspend must be genuinely durable" as a testable claim, not an assumption: the completion-confirmation test resumes the graph via a freshly opened `PostgresSaver` connection and a newly compiled `TreatmentPlanWorkflow`/graph object — deliberately not the same in-process object that created the suspend — so the test would fail if the suspend only worked by accident of holding the same Python object in memory. This directly matches the slice's own most important acceptance criterion (durability, not just code-path coverage) and the general pattern captured in the new `sdlc-architecture-service-integration-contract` skill.
- Followed the existing Protocol/stub/live adapter pattern exactly for `TreatmentSuggestionProvider` (only a stub exists — HiveSight has no real endpoint yet), consistent with every other external dependency in this codebase.
- All four previously signed-off Gherkin scenarios pass via `TestClient` (no `.feature` file — plain, descriptively-named pytest functions with the exact scenario text in each docstring, matching this project's existing convention for API-only slices like `test_query_submission_slice.py` rather than introducing pytest-bdd machinery that nothing else in this repo uses yet).
- Wired LangGraph's own checkpoint-table setup into the existing `db.py` CLI (`migrate`/`migrate-test`/`reset-test`), as an explicit step alongside `apply_migrations` — not automatic at app startup, matching this project's established "migrations run explicitly" convention rather than adding new implicit behavior.
- Full backend suite green throughout (61 passed, 4 skipped — pre-existing live-API tests requiring real keys — after every cycle), `ruff` clean after an auto-fix pass on import ordering.
- Closeout: updated `CONTEXT.md` (`Proposed Treatment` term), `requirements/decision-log.md` (new entry), `requirements/traceability.md` (FR-009 now Covered, FR-010 marked Superseded per the system-of-record split, FR-011 Deferred with its scope-widening noted), the slice doc's Acceptance Criteria (all checked, plus an Implementation Notes section documenting the two deviations from the original sketch — the system Workspace decision and `hive_id`-not-`ProposedTreatment`-id on the completion endpoint), `.env.example` (new `ADVISOR_API_HIVESIGHT_SERVICE_KEY` placeholder), and the shared `hivesight-advisor-integration-contract` skill (status table updated from "planned" to built, with real endpoint paths/payloads now that they exist).

Human judgment still required:

- HiveSight's own two endpoints (accept-suggestion, completion webhook) are not built — this slice only proves the Advisor's side against stubs. Real end-to-end integration testing waits on that work landing on HiveSight's side.
- The service-to-service auth mechanism (static shared secret) is deliberately the lightest option for one known caller; revisit if a second external caller or credential-expiry need ever appears (already named as the upgrade path, not scheduled work).

### 2026-08-05 US Corpus Growth (Api-Bioxal), Plus a Real `corpus_admin` Bug Found By Using It

Human direction: "Add more US corpus content" — lean-process work per the standing preference.

AI contribution:

- Researched a real, verifiable US EPA-registered oxalic acid product (Api-Bioxal — EPA reg. 91266-1-73291) via WebSearch against EPA's own label PDF and a retailer product page, then added it via the existing Corpus Curator CLI (`corpus_admin add-document`) with its AI-assisted review step.
- The review flagged two real, worthwhile wording issues (an undated exclusivity claim that would silently go stale; organic-certification phrasing less precise than the existing HopGuard entry's wording) — applied both before finalizing, since they were cheap fixes to a legitimate precision concern, not scope creep.
- In the process of running the CLI from `services/advisor-api/` rather than the repo root, discovered a genuine bug: `corpus_admin.DEFAULT_DATA_FILE` was a bare relative path (`"scripts/curator_added_documents.yaml"`), so it silently wrote a second, stray copy of the ledger relative to cwd instead of updating the single canonical, source-controlled file — directly undermining the "fully reproducible from a fresh clone" guarantee the Corpus Curator CLI Tooling decision was built around. No existing test caught this because every test passes an explicit `data_file` path, never exercising the default.
- Fixed via TDD: a regression test asserting the default resolves to an absolute, package-anchored path regardless of cwd, then anchored `DEFAULT_DATA_FILE` to `Path(__file__).parents[4]` instead of a bare string.
- Reconciled the resulting divergence by hand: merged the new entry into the canonical YAML (with the two wording fixes applied), deleted the stray duplicate file, and re-embedded the corrected passage text in the live dev database via Voyage so the DB and the source-controlled ledger describe the exact same content.
- Verified: full backend suite green (62 passed, 4 skipped) and `ruff` clean throughout.

Human judgment still required:

- FR-006 (source conflict detection) still has no content — no genuine real-world disagreement between two authoritative sources has turned up in either the UK or US research pass.

### 2026-08-05 Slice 0009: Reject-And-Revise Loop (First Genuine Cycle In A LangGraph)

Human direction: "Scope the reject-and-revise loop" — then, before implementation, "grill me first," explicitly invoking the `productivity-grilling` skill on the already-scoped design rather than proceeding straight to TDD.

AI contribution:

- Initial scoping grilled six decisions as usual (endpoint shape, reason-feeding mechanism, revision cap, exhaustion behaviour, append-only persistence, re-triggering `Suggest` per revision), then drafted and got sign-off on three Gherkin scenarios.
- The user's "grill me first" request was treated as its own distinct checkpoint — a second grilling pass on the already-agreed design, using the `productivity-grilling` skill's one-question-at-a-time-with-a-recommendation format, before any implementation began. This surfaced four real gaps the first pass had missed: whether hitting the revision cap should end the episode entirely (it shouldn't — the last suggestion must stay acceptable) or foreclose only further revision; an exact off-by-one in what "cap at 3" means (3 revisions on top of the original, not 3 suggestions total); a load-bearing mechanical consequence of the first point — a rejection at the cap can't be allowed to actually resume the graph, since LangGraph's interrupt is a one-shot consumption with no "un-pause," so the endpoint has to peek at graph state before deciding whether to resume at all; and a fourth Gherkin scenario for what happens when a *revision itself* comes back ungrounded, which none of the original three scenarios covered.
- This validates deferring TDD until after a design is genuinely pressure-tested, not just agreed to on the first pass — three of the four gaps found were exactly the kind of edge case that would otherwise have surfaced mid-implementation or, worse, shipped silently wrong (a rejected-but-still-should-be-acceptable suggestion being lost forever is a real usability bug, not a cosmetic one).
- Implemented via TDD in four cycles: repository (`mark_rejected`, `save(supersedes_proposed_treatment_id=...)`), the graph itself (`_wait_and_resume` now branches on an `action` field and conditionally loops back to `recommend`), the router endpoint, and closeout.
- One test-tuning discovery along the way, not a production bug: the existing shared test fixture seeds passages with an all-zero embedding placeholder, which pgvector's cosine distance treats as trivially close to any query — fine for the "always grounded" tests that had relied on it, but unable to ever produce a genuine ungrounded result. Built a second fixture that actually embeds the passage text via the stub provider for the one test that needed real distance behaviour, rather than weakening the assertion or forcing the shared fixture to change (which risked destabilizing every other test depending on its current behaviour).
- The exhaustion test is the one that actually proves the grilling's key finding: it drives 4 real rejections through the workflow, then calls `confirm_completed` on what should still be the last (3rd-revision) suggestion — if the peek-before-resume mechanic were wrong, this test would fail, not just look plausible.
- Full backend suite green throughout (72 passed, 4 skipped), `ruff` clean. Closeout: decision-log gained a 10-point entry (6 original + 4 follow-up), traceability's FR-009 row now covers both slices' scenarios, `CONTEXT.md`'s `Proposed Treatment` term already anticipated the rejected status from scoping, and the shared `hivesight-advisor-integration-contract` skill gained a fourth contract row for the new rejection endpoint.

Human judgment still required:

- `MAX_REVISIONS = 3` is an explicit judgment call, not calibrated against any real usage — worth revisiting once there's real negotiation behaviour to observe.
- The rejection reason is not accumulated across revisions (only the latest is used) — a reasonable default reading of the slice doc's wording, but not something that was separately grilled; worth confirming if it ever produces a confusing revision in practice.

### 2026-08-05 Slice 0010: Voyage Retry With Backoff (Adapter-Level, Not LangGraph)

Human direction: "Scope the retry-with-backoff slice" — following the earlier "what else could LangGraph demonstrate" discussion, which had originally framed this as a LangGraph pattern.

AI contribution:

- Before scoping, flagged a real tension the earlier framing had glossed over: `VoyageEmbeddingProvider` is called from both the plain web-UI query flow and the agentic `TreatmentPlanWorkflow`, so a retry built as a LangGraph node would only protect the newer, less-used path and leave the actual problem (hit for real during threshold calibration, on the plain query path) unfixed. Recommended the adapter-level fix instead, explicitly naming the trade-off (losing a "third LangGraph pattern" for portfolio purposes, in exchange for actually closing the real roadmap item) rather than silently picking one.
- Grilled five decisions (placement, retryable-vs-not error classification, backoff shape, scope limited to Voyage, test seam), all agreed without pushback.
- Skipped the Gherkin scenario-signoff step deliberately — this is genuinely internal-only behaviour (the Beekeeper-visible Answer is identical regardless of how many attempts Voyage needed), matching the existing convention's own carve-out for pure internal changes.
- Implemented in one TDD cycle: an injectable `client` parameter (same constructor-injection seam already used throughout this codebase) plus an injectable `wait` parameter so tests never sleep for real. All three tests (retry-then-succeed, exhaust-and-raise, non-retryable-fails-immediately) passed on the first implementation attempt.
- `tenacity` was already an implicit transitive dependency (via `langchain-core`, pulled in for Slice 0008's LangGraph work) — promoted to an explicit direct dependency now that this codebase imports it directly, rather than relying on another package's dependency tree to keep providing it.
- Verified no regressions: full backend suite (75 passed, 4 skipped), `ruff` clean, no changes needed to any caller.

Human judgment still required:

- The backoff numbers (4 attempts, 1–8s exponential with jitter) are a standard, defensible shape, not calibrated against Voyage's actual free-tier rate-limit recovery time — worth revisiting if it proves too short or too long in practice.
- `ClaudeGenerationProvider` has the same gap (no retry handling) but was deliberately left out of scope, since no real problem has surfaced there yet.

### 2026-08-06 Cross-Repo Review Of HiveSight's Slice 0029.5 Found A Real Advisor-Side Bug

Human direction: "please review and comment in a durable response doc" for HiveSight's Slice 0029.5 (Advisor Treatment Recommendation Intake) design.

AI contribution:

- Rather than answering HiveSight's six review questions from memory of how Advisor's endpoints work, verified each one directly against the current code (`routers/hivesight_integration.py`, `adapters/generation_claude.py`) before answering — confirmed the exact request/response shapes, confirmed no inline citation markers exist in answer text (a real rendering-assumption gap HiveSight's UI work would otherwise have hit later), and confirmed no jurisdiction-discovery endpoint exists.
- One question (whether a second top-level treatment-plan request while an earlier one sits unresolved causes a problem) wasn't answerable from reading code alone, since it depends on LangGraph's actual re-invoke behaviour on an existing thread — not something to reason about from first principles with confidence. Built a small throwaway script against the real Postgres-backed checkpointer to test it directly: confirmed a second `request_treatment_plan` call for the same `hive_id` silently creates a second, unlinked `Proposed Treatment` row and permanently orphans the first one (still `suggested`, but unreachable via the existing lookup, forever). This is a real bug in Advisor's own Slice 0008/0009 implementation, not a HiveSight design question — found only because Slice 0029.5's explicit choice ("does not notify Advisor when a recommendation is accepted or declined... belongs to a later slice") makes the scenario that triggers it a near-certainty once the integration is used for real, rather than an edge case.
- Recommended a fix direction (idempotent-per-hive request handling) that mirrors the idempotency HiveSight had already independently chosen for its own side, rather than inventing a new pattern — consistency across the two systems was itself part of the recommendation, not just correctness.
- Flagged the `jurisdiction_id`-as-raw-UUID contract weakness (no discovery endpoint exists, confirmed by checking for one) as a second, independent finding — this one was catchable by reading code plus reasoning about what a cross-service caller could actually know, not something requiring empirical testing.
- Wrote the response as a durable doc (`requirements/hivesight-slice-0029-5-review-response.md`) rather than only a chat reply, consistent with the pattern established for the Slice 0029 review, and logged the two real findings as candidate follow-up slices in `requirements/roadmap.md` rather than fixing them inline as part of a review task.

Human judgment still required:

- Whether to scope and grill the idempotent-request fix as its own vertical slice now, or wait until HiveSight's Slice 0029.5 is closer to real implementation.
- Whether to change `jurisdiction_id` to a code-based lookup is itself a real API-contract decision (backward compatibility for any future real caller) that deserves its own grilling pass, not a quick patch.

### 2026-08-06 Slice 0011: Treatment Plan Readiness (Closing Four Cross-Repo Review Findings)

Human direction: "can you plan and design a 'Treatment Plan Readiness slice' addressing" the four Advisor-side gaps found in the two HiveSight review-response docs, "and in the design include any contract alterations so I can pass them back to Hive-sight."

AI contribution:

- Grilled four decisions before implementation, each grounded in a direct code check rather than assumption: confirmed `jurisdiction_id` is threaded deeply through internal RAG plumbing (so the fix stays at the API boundary only, translating via a new small `JurisdictionRepository`, not touching `AnswerQueryWorkflow`/`CorpusRepository`); confirmed no existing jurisdiction-discovery endpoint exists anywhere (the actual problem being fixed); worked out that graph-state fields alone can't reliably distinguish "still pending" from "fully completed" for the idempotency fix, so the fix goes through the repository's authoritative status instead.
- Implemented via TDD in four cycles (repository, workflow idempotency, router contract, closeout). The idempotency fix mirrors `reject_treatment`'s existing peek-before-resume pattern rather than inventing a new mechanism — architectural consistency was itself part of the design, not an afterthought.
- Treated this as a deliberate breaking change to the request contract (`jurisdiction_id` → `jurisdiction_code`), not an additive/backward-compatible one, since no real caller exists yet and carrying the brittle UUID forward "for compatibility" would help no one. Updated the pre-existing Slice 0008/0009 tests to the new shape rather than leaving two contract versions to reconcile later.
- The slice doc includes a dedicated "Contract Changes For HiveSight" section with the exact new request/response JSON shapes, written specifically to be copy-pasted into a message back to the HiveSight side, per the user's explicit ask.
- Closeout updated both review-response docs in place (added "resolved, see Slice 0011" notes at the top rather than rewriting them, preserving the original review as a historical record) and the shared `hivesight-advisor-integration-contract` skill with the real, implemented shapes — plus one still-open item carried forward explicitly (the header-name collision, which is HiveSight's own fix, not resolved by this slice).
- Verified: full backend suite (85 passed, 4 skipped), `ruff` clean, no regressions to Slice 0008/0009's own behavioural guarantees.

Human judgment still required:

- Whether to actually send the "Contract Changes For HiveSight" section (or the whole slice doc) back to whoever owns the `hive-sight` repo, and in what form (comment, message, doc).
- The header-name collision flagged in the Slice 0029 review remains genuinely unresolved — it's on HiveSight's side to fix, not something Advisor can close unilaterally.

### 2026-08-06 Slice 0030 Review: First Real Use Of The New Cross-Project Review Skill

Human direction: pasted HiveSight's Slice 0030 (Dual-Seam Acceptance Specification Pilot) alignment doc directly into chat, following the earlier "warn HiveSight" exchange — this was HiveSight's session responding in kind, having picked up the newly-shared skills.

AI contribution:

- Applied `sdlc-architecture-cross-project-contract-review` (written earlier this session) for the first time on an inbound proposal, rather than improvising a fresh review approach: pulled the shared skills repo first to see HiveSight's actual already-pushed skill edits (not just the summary doc), verified they were appropriately scoped (generic content in the generic skill, HiveSight specifics in the HiveSight-specific one) before commenting.
- Verified Advisor's own current state directly (grep for `pytest_bdd` usage, current router endpoints, repository lookup methods) rather than answering from memory of having built Slice 0011 minutes earlier — confirmed no pytest-bdd wiring exists and no recommendation-history endpoint exists, both directly relevant to the alignment questions asked.
- Found a structural mismatch the proposal itself didn't address: HiveSight's proven pattern is same-repo/two-clients (one `.feature` file, two bindings, both owned by HiveSight); what's being proposed for the Advisor boundary is two independently-versioned repos with no shared client — a materially different, harder problem with no established solution for where a "shared" file would actually live without reintroducing drift. Recommended prose-sharing in the living contract skill instead of file-sharing, rather than either rejecting the pattern outright or adopting it uncritically.
- Caught a real scope tension between the incoming doc and HiveSight's own earlier Slice 0029.5 design (which explicitly chose not to call Advisor's completion/rejection endpoints) — the new doc's "beekeeper accepts/declines" bullet implies the opposite. Flagged as an open question rather than assuming either reading.
- Per the review skill's own rule, made no code changes and did not update the shared living contract skill — this review didn't result in any new implemented behaviour, only a scoping response.

Human judgment still required:

- Whether HiveSight actually wants Advisor's recommendation-history endpoint, or whether HiveSight's own snapshotting already covers the audit need.
- The accept/decline routing question above.
- Whether the prose-in-shared-skill recommendation satisfies what HiveSight was actually after, or whether they'll push back toward the file-sharing approach once a third capability makes the same-repo pattern more attractive to extend.

### 2026-08-07 Web Acceptance Feature Files Migrated To Capability-Based Naming

Human direction: prompted by reviewing HiveSight's own capability-catalogue migration and their stated motivation — not a bug found, but the concern that slice docs are point-in-time records, and a test file named after the slice that introduced it gives no signal about whether it's still the live description of current behaviour once later work supersedes it. Confirmed this had already happened for real in this repo: Slice 0011 required editing the Slice 0008/0009 tests in place when the request contract changed.

AI contribution:

- Moved all six web acceptance feature files from `vertical_slice_NNNN_*.feature` naming into capability directories (`grounding/`, `jurisdiction/`, `provenance/`, `corrections/`, `treatment/`), matching HiveSight's own `acceptance/features/<capability>/...` convention. Renamed the paired step files to match. Used `git mv` throughout so history is preserved, not lost to a delete+add.
- Updated both Playwright configs' feature glob from `*.feature` to `**/*.feature` to reach the new subdirectories; confirmed via `playwright.live.config.ts`'s `grep` filter (which matches `Feature:` title text, not file paths) that the live-pass config needed no further change.
- Updated `requirements/traceability.md`'s seven pointers to the new paths, and added an explicit naming rule to the project-local `requirements-traceability` skill: feature files are named by capability, never by slice, with the reasoning stated plainly so a future session understands *why*, not just the rule.
- Verified the migration didn't break anything by actually running the suite (not just trusting the mechanical rename): 9 of 10 scenarios passed. The 10th (treatment trade-off comparison) failed — before concluding anything, confirmed via `git stash` that it fails identically against the pre-migration commit, proving it's a pre-existing issue the migration surfaced by being the first full run this session, not something the rename caused.
- Did not silently work around or ignore the pre-existing failure once found. Logged it as its own roadmap item (distinct from the existing, related-but-different live-pass threshold-drift item — this is the *stub* suite returning zero citations, a more severe symptom than the live suite's partial/ungrounded ambiguity) and, per the traceability skill's own "be honest about what Covered actually proves" rule, changed FR-004's traceability row from "Covered" to an explicit failing-scenario warning rather than leaving a green checkmark next to a red test.

Human judgment still required:

- Root-cause the treatment trade-off comparison failure (stub embedding distance drift is the leading hypothesis, unconfirmed) and decide the fix.
- FR-004 should not be considered demonstrated again until that scenario passes and its traceability row is restored to Covered.

### 2026-08-07 Treatment Trade-Off Comparison Failure Root-Caused: A Test Bug, Not Drift

Human direction: "dig into it" — following up on the treatment trade-off comparison failure logged earlier the same day, where the initial hypothesis (recorded honestly as unconfirmed) was stub-embedding threshold drift, by analogy with the already-documented live-pass drift finding.

AI contribution:

- Did not act on the drift hypothesis without checking it. Computed the actual stub-embedding cosine distances for the real scenario query against all four UK passages directly, rather than reasoning abstractly about "corpus growth." Result: closest match (Apivar) at 0.67, comfortably within the partial threshold (0.8) — meaning the retrieval/grounding logic should have retrieved and cited multiple documents, contradicting the "drift" hypothesis outright.
- Given the hand-calculation didn't match the observed failure, didn't stop at "well, my theory says it should work" — went to the actual captured evidence from the failed run (`error-context.md`'s page snapshot) rather than re-running blind. That snapshot showed the "Asking..." button still disabled at the moment of assertion — direct evidence the request was still in flight, not that grounding had failed.
- Confirmed the real root cause by comparing against every other (passing) step file's pattern: all of them wait for `.answer-view` to become visible (an auto-retrying assertion) before reading any further content; the failing step skipped straight to `allTextContents()`, which reads the DOM once with no wait at all.
- Fixed the step definition to match the established pattern, verified in isolation (scenario alone) and then the full suite (10/10 passed).
- Went back and corrected both `requirements/roadmap.md`'s entry and `traceability.md`'s FR-004 row rather than leaving the earlier, now-disproven drift hypothesis on record — an incorrect diagnosis left unretracted would be actively misleading to a user who relies on these docs instead of reading code.

Human judgment still required:

- None — this one closed cleanly. Worth noting as a process point: the earlier finding was logged with appropriate uncertainty ("not yet root-caused," "plausibly," "needs its own investigation") rather than asserted as fact, which made correcting it later a clean edit rather than a retraction of something stated too confidently.

### 2026-08-07 "CI Pipeline" Roadmap Item Was Stale — Verified Before Building Anything

Human direction: asked what's next in the backlog; AI recommended the CI pipeline item based on the roadmap's own text ("No `.github/workflows` exists yet").

AI contribution:

- Before starting any work, checked the actual repo state rather than proceeding straight from the roadmap's claim — found `.github/workflows/ci.yml` already exists, dated 2026-08-03, well-structured (three jobs matching the project's real test surfaces: backend pytest+ruff, web typecheck+Vitest, acceptance Playwright+Gherkin).
- Checked actual run history via `gh run list` rather than assuming "exists" meant "works." Found one red run (Slice 0011) and investigated rather than either ignoring it or assuming it indicated a real problem — `gh run view` showed GitHub-side infrastructure failures ("job was not acquired by Runner," "Service Unavailable"), not a code or test failure. Every other run, including everything from this session's LangGraph/HiveSight-integration work, has passed.
- Corrected the stale roadmap line rather than silently building a second/redundant CI setup to match a recommendation that turned out to be based on inaccurate information.

Human judgment still required:

- None from this finding — genuinely closed. Worth noting as a process point: this is exactly why "verify against real state before recommending or building" matters even for something as low-stakes as picking the next backlog item, not just for code changes — recommending a real chunk of work based on an unverified doc claim would have wasted real effort building something that already existed.

### 2026-08-07 Grounding Threshold Recalibration: Measured, Not Guessed, Then Decided Not To Adjust

Human direction: picked up the previously-logged threshold-drift finding as the next backlog item; after reviewing real measurement data and three explicit options, chose to defer further threshold changes until passage chunking exists.

AI contribution:

- Rather than picking new threshold numbers from intuition, built a small measurement script and ran 11 hand-picked test queries (spanning grounded/ambiguous/ungrounded intent, both jurisdictions) against the *real* Voyage embedding model and the *current*, grown corpus — paced under the free-tier rate limit (21s between calls, embeddings cached so each unique text was only embedded once) rather than either burning through the rate limit or falling back to the stub, which would have measured the wrong thing entirely.
- The data reproduced the original drift finding exactly (0.4548) and showed it wasn't a one-off — a second independent off-topic query showed the same pattern. But went further than confirming the known finding: noticed the "ambiguous" and "ungrounded" test categories didn't actually separate cleanly in the real numbers (an off-topic UK query scored *closer* to source material than a genuinely-related one), which meant the obvious fix — nudge the threshold — wouldn't actually solve the problem cleanly. Surfaced this complication honestly rather than presenting a simpler, tidier story than the data supported.
- Traced that complication to a plausible structural root cause (one Passage per Corpus Document today, so a whole document collapses into a single distance measurement) rather than stopping at "the numbers don't separate cleanly, huh." This connected the finding to an already-existing, previously-unrelated roadmap item (passage chunking) that turned out to be the actual prerequisite for a real fix.
- Presented three genuinely distinct options with reasoning rather than pushing a single recommendation on what is partly a product-values question (whether a visibly-caveated `partial` label is an acceptable outcome for an off-topic question) layered on a technical one — user chose directly, no further negotiation needed.
- Explicitly relinked the two roadmap items (threshold recalibration and passage chunking) so their dependency is visible to a future session, not just implied.

Human judgment still required:

- None immediately — genuinely decided and closed for now. Revisit trigger is explicit: once chunking exists, this becomes a real, actionable decision again, not before.

### 2026-08-07 Passage Chunking: Surfaced A Real Scope Mismatch Before Writing Any Code

Human direction: "let's go with passage chunking" — picked up the just-decided prerequisite for the threshold recalibration.

AI contribution:

- Before scoping the slice, read the actual seeded documents rather than trusting the roadmap's own framing. Found every existing Passage was already a single short paragraph with nothing to split — meaning "chunking today's documents" as literally described wouldn't touch the measured threshold problem at all, despite the decision log naming chunking as its prerequisite. Surfaced this contradiction directly instead of silently scoping a slice that would technically satisfy the roadmap item's letter while missing its actual point.
- Grilled two genuinely separate design forks with the user rather than picking defaults: (1) build chunking as speculative forward-looking infrastructure vs. drop it vs. prove it against one real long document first; (2) curator-driven manual chunking vs. an automatic splitter. Both had real trade-offs and no objectively correct answer, so both went to the user rather than being decided silently.
- During implementation, ran the real curator review flow (live Claude, not a stub) for the new document's three passage chunks — and it caught an actual drafting error: chunk 2's original text implied both Apivar and Apiguard carry a temperature restriction, directly contradicting the existing Apivar passage which explicitly states no such restriction. Retired the mistakenly-committed document, cleaned up the dev database and curator YAML by hand rather than leaving the bad row as a "retired" artifact, and re-added with corrected text — demonstrating the AI-assisted review step (Slice 0006) catching a genuine content bug, not just rubber-stamping.
- Discovered mid-implementation that the web citation UI renders only `document_title`, never Passage text — meaning the originally-planned Gherkin scenario for "cites the specific sub-topic Passage" was unwritable as a meaningful UI assertion (two sibling Passages render identical citations). Rather than forcing a scenario that would pass without actually testing anything, dropped it and documented why in the slice doc, relying on the `CorpusRepository` test instead — the seam where chunking's value genuinely lives.

Human judgment still required:

- None immediately. Two real follow-ups were explicitly logged rather than actioned: re-running the threshold measurement against the new multi-topic document (a distinct next step, not assumed to happen automatically), and Passage-level citation display in the UI, if that ever becomes an actual product need.

### 2026-08-07 Threshold Re-Measurement: The Working Theory Was Wrong, Said So Directly

Human direction: "re-run the threshold measurement against the new document" — the explicitly logged follow-up from the chunking slice.

AI contribution:

- Extended the existing measurement script rather than rewriting it: pulled the new chunked document's passages dynamically from the curator YAML (now a list per document, post-Slice-0012), added three new queries specifically targeting each sub-topic chunk, kept the original 11 queries unchanged for a clean before/after comparison, and preserved the same 21-second-paced, cached-embedding methodology.
- The result split into two different findings, and both were reported, not just the convenient one: sub-topic retrieval precision worked exactly as designed (all three targeted queries hit their intended chunk), but the threshold-separation problem — the actual reason chunking was built — got measurably *worse*, not better. The three off-topic UK queries all moved closer to the corpus after chunking landed, the opposite of the prior decision log entry's stated expectation.
- Rather than quietly filing this as "inconclusive" or re-framing the chunking slice as successful on the strength of the sub-topic result alone, went back to the decision log and retracted the specific claim that had turned out to be wrong — "passage chunking would sharpen resolution and separate relevance tiers" — with a concrete explanation of the likely actual mechanism (narrower per-passage scope, but broader corpus-wide topic coverage, are two different and partly opposed levers). Presented this as a genuine correction to a previously-recorded piece of reasoning, not a new decision layered on top of an unexamined old one.
- Gave the user three real options (correct the record and stop since nothing is broken; investigate further with a specific untested hypothesis; pivot to the product-framing question already parked in the original entry) rather than picking one, since which is worth the effort is a value judgment, not a technical one.

Human judgment still required:

- None immediately — user chose to correct the record and stop, since nothing is currently misclassifying and no further hypothesis was ready to test. The problem is now explicitly logged as open with no known fix, not silently reframed as solved or quietly dropped.

### 2026-08-07 Guest Access And Rate Limiting: A Cost Question Became A Domain-Model Question

Human direction: picked "real user authentication" as the next backlog item, then immediately raised a genuine cost concern in passing — should unauthenticated guests be allowed to use the system at all, given every query costs real money across two paid APIs.

AI contribution:

- Recognised the user's spoken concern as a real, undecided product/cost trade-off rather than a rhetorical aside, and grilled it directly (guest access allowed at all? rate-limited or not?) before writing anything, rather than picking a sensible-sounding default and moving on.
- Before scoping further, read the actual `/queries` router and found a real, non-obvious blocker: every query already required a client-supplied `workspace_id` and an active Workspace Membership, with no "no Workspace" path anywhere in the domain model. A guest has no login and therefore no Membership — "just allow guests" wasn't actually implementable without first deciding how a guest's activity fits `CONTEXT.md`'s existing "Workspace is the ownership boundary for queries" invariant. Surfaced this before writing the slice doc rather than discovering it mid-implementation.
- Proactively suggested splitting "real user authentication" into two slices — guest access/rate limiting (buildable now, no OIDC needed) and real Google sign-in (a much larger, separate design surface) — rather than letting the original single backlog item balloon into an oversized slice covering both. Got explicit confirmation before acting on the split, since it changed the shape of what the user had originally asked for.
- Caught a real regression during implementation, not just at review: after making `/queries` guest-only (dropping `workspace_id` from the request), the Correction flow's hardcoded dev-identity constants silently stopped matching the Answer they were meant to correct (now always Guest-Workspace-owned), causing every correction submission to 404. Found this by actually running the full acceptance suite rather than assuming the isolated unit/integration tests were sufficient, fixed it, and documented it explicitly in both the slice doc and roadmap rather than letting a silent fix go unrecorded.
- Recognised a second implementation-time constraint before it caused a flaky or contaminating test: the rate limiter is a deliberate process-wide singleton, and the acceptance suite runs every scenario sequentially against one shared server process — a naive Gherkin scenario for "guest exceeds the limit" would have poisoned every other scenario's query budget in the same run. Resolved by proving the exceeded-limit behaviour at the unit and integration seams instead (with a scoped dependency override, not the shared singleton) and setting the suite's configured limit deliberately high — the same "right seam for the claim" reasoning already established in the Slice 0012 closeout, applied consistently rather than re-litigated from scratch.

Human judgment still required:

- None immediately — every design fork was grilled and resolved, the regression was caught and fixed within this same pass, and the follow-on item (real Google OIDC sign-in) is explicitly logged as its own not-yet-scoped roadmap item, not assumed to happen automatically.

### 2026-08-07 Google OIDC Sign-In: A Deterministic Test Strategy For An Undeterministic External Auth Provider

Human direction: "scope real Google OIDC sign-in" — the remaining half of the original "real user authentication" item.

AI contribution:

- Before grilling design questions, verified the actual constraints rather than assuming a familiar OAuth pattern would apply cleanly: checked both `pyproject.toml` and `package.json` to confirm this was genuinely greenfield (no JWT/session library anywhere), and checked the CORS middleware to confirm `allow_credentials` wasn't set — meaning a cookie-based session wasn't even viable today without extra config, a concrete fact that fed directly into the session-transport grilling question rather than being asserted from general knowledge.
- Solved the real engineering problem of testing signature verification against an external identity provider deterministically: rather than either skipping verification-logic tests entirely or depending on live Google network calls in CI, used `google-auth`'s own injectable `request` transport parameter to serve a locally-generated JWKS matching a self-signed test token — proving the *real* verification library's behavior (wrong audience, wrong issuer, expired token, unknown signing key) without any live dependency. Verified this approach worked with a standalone throwaway script before committing to it in the actual test suite, rather than discovering a dead end mid-TDD.
- Surfaced a second real library-selection fork mid-implementation: `google-auth`'s JWK-format certs path lazily imports `pyjwt`, which wasn't installed — rather than silently reaching for a workaround, added it as an explicit declared dependency once confirmed necessary.
- Hit a genuine, non-obvious test-infrastructure conflict once the frontend/backend wiring was done: the two pre-existing browser-level correction-submission scenarios (Slice 0005) could no longer be driven through the UI, since real Google sign-in can't be automated in Playwright without either driving Google's actual consent screen or adding a bypass to the app. Rather than quietly picking one (especially the bypass, which is a real security-relevant code change), stopped and grilled it directly with the user, naming the trade-off honestly (bypass code in production vs. real coverage loss) rather than downplaying either side. This mirrors the "right seam for the claim" pattern from Slices 0012/0013, but is a meaningfully higher-stakes instance of it — the earlier cases were about *proving new* behavior at the right seam; this one is about *accepting the loss* of previously-existing browser-level coverage, which deserved the user's explicit sign-off rather than being silently absorbed as "just another implementation detail."

Human judgment still required:

- The Google Cloud OAuth Client ID precondition still needs creating before the live-browser verification pass can run — flagged clearly in the slice doc, roadmap, and acceptance criteria as the one remaining open step, not silently treated as done.
- Signing out and the cross-project alignment note to HiveSight (both explicitly named as still-open in the original pre-slice discussion) remain unscoped — logged, not actioned.
