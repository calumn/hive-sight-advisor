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
