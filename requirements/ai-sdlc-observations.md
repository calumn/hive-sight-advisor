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

This closes every item in `architecture/domain-model.md`'s and `architecture/system-context.md`'s Open Architecture Questions sections. Next phase is a first vertical slice, human's call.

AI contribution (cost pass):

- Searched current Fly.io and Render pricing rather than answering from memory, since hosting prices change and the human's question was explicitly about present-day cost.
- Distinguished hosting cost (platform-dependent, roughly comparable across Fly/Render/AWS at this scale) from usage-based provider cost (Claude generation, Voyage AI embeddings — scales with query volume, tracked separately, not a factor in the platform decision) so the two weren't conflated in the comparison.
