# Decision Log

## 2026-07-31 V1 Scope Boundary

**Decision**: V1 scope is Phase 1 (Grounded Knowledge) only. Phase 2 (the Advisor) is explicitly deferred to a later release and does not begin until Phase 1's grounding and citation behaviour is trusted.

**Why**: Matches the vertical-slice discipline already established on HiveSight — one thing proven before the next depends on it. Phase 2's proposals are only meaningful if the retrieval layer underneath them is already trusted; building both at once would make it impossible to tell whether a bad Phase 2 suggestion was an advisor problem or a grounding problem.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Primary Persona And Multi-User Modelling

**Decision**: Correcting the initial recommendation — this follows the same pattern as HiveSight, not a permanently single-user tool. Model `Workspace`, `Workspace Membership`, and roles the same way HiveSight does from the start. Real authentication remains deferred, same as HiveSight's dev-header approach, but the domain shape assumes multiple users from day one rather than assuming one and retrofitting later.

**Why**: HiveSight itself already draws this distinction — multi-user is the intended shape, single dev-auth user is just the current implementation depth. Consistency in how both projects handle this saves having to relearn or reconcile it later, and roles/workspace modelling is cheap; authentication is the expensive part, and that's what's actually being deferred.

**Open follow-on**: whether the Advisor's `Workspace` concept is independent of HiveSight's, or whether access to the Advisor is gated through an existing HiveSight `Workspace` — raised in conversation, not yet resolved (see next grilling question).

**Resolved via**: grilling session with Claude.

## 2026-07-31 V1 Jurisdiction Scope

**Decision**: V1 corpus covers US and UK only. Full EU coverage is explicitly deferred, and when it is added it must be modelled at member-state granularity, not as a single "EU" bucket, because pesticide/veterinary product registration is frequently decided nationally under the EU framework rather than centrally.

**Why**: FR-003 (no blending guidance across jurisdictions) is only testable with at least two jurisdictions that can genuinely disagree, so starting with a single jurisdiction would undercut an already-confirmed requirement. US (HBHC) and UK (APHA BeeBase) each have one strong, well-defined central source, which is enough to prove the disambiguation mechanism works before taking on the added modelling complexity of the EU's national-level fragmentation.

**Resolved via**: grilling session with Claude.

## 2026-07-31 No-Grounding Behaviour

**Decision**: When no relevant grounding exists for a question, the system must not answer from unsourced general knowledge. It states plainly that it has no grounded answer, and offers the closest related grounded material if any exists, clearly labelled as partial rather than a direct answer. Captured as FR-008.

**Why**: Follows directly from FR-002 (every answer must cite a source) — an ungrounded answer already contradicts a confirmed requirement, not a new trade-off. A hard refusal with nothing else risks feeling broken; silently blending in unsourced general knowledge undermines the trust premise the vision is built on the first time someone notices it happened.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Advisor Independence From HiveSight

**Decision**: The Advisor is architecturally and logically independent of HiveSight. It may use HiveSight as an optional data source (Phase 2, FR-010) where available, but does not require it and is not gated behind a HiveSight `Workspace`. A commercial or packaging tie-in between the two products is possible later, but that is a business decision to make explicitly if and when it arises — it is not an architectural dependency baked into v1.

**Why**: Phase 1 is a knowledge/Q&A capability with no HiveSight-shaped reason to inherit HiveSight's authorization boundary. A separate repo was already a deliberate choice. Keeping the two logically separate now keeps a future integration cheap and optional rather than assumed.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Correction Trust Level For V1

**Decision**: Corrections (FR-007) are modelled as workspace-scoped, consistent with FR-000, but every correction is treated as trusted evidence directly for v1, with no separate human review gate.

**Why**: HiveSight's user corrections need a review gate because they can come from anyone with a Workspace and directly affect training data quality at scale. Here, in practice there is a single real user for the foreseeable future, who is also the domain expert able to judge correctness — a review gate would just be self-review. The gate is worth keeping as a real concept in the domain model so it is cheap to switch on once other users exist, but not worth enforcing against a population of one.

**Resolved via**: grilling session with Claude.

This closes the initial grilling round — every open question carried from the first draft is now resolved.

## 2026-07-31 Terminology Note: "Advisor" Naming Collision With HiveSight

**Observation, not a decision requiring action yet**: HiveSight's own `CONTEXT.md` already lists `advisor` as a future Workspace Membership role name (alongside `member`, `inspector`, `reviewer`). That is a different concept from this product's name, "HiveSight Advisor" — a role a person holds inside a HiveSight Workspace, versus the name of this separate product. Caught while cross-checking `architecture/domain-model.md` against HiveSight's `CONTEXT.md` for contradictions, per the alignment discipline this project committed to.

**Why it's flagged rather than fixed**: Neither project currently defines the colliding term in a way that actively contradicts the other — HiveSight's `advisor` role is unimplemented/future, and this product's name is not a domain term inside HiveSight's model. No renaming forced today. Worth remembering if HiveSight ever implements the `advisor` Workspace role and this product's documentation is being read alongside it, since a reader could reasonably conflate "an advisor of a HiveSight Workspace" with "HiveSight Advisor the product."

**Resolved via**: self-caught during domain-model cross-check, per `sdlc-architecture-domain-language`'s instruction to challenge terminology conflicts immediately rather than let them sit.

## 2026-07-31 V1 Application Surface

**Decision**: Web app, backed by a real API rather than logic embedded directly in the UI layer.

**Why**: Confirmed as the recommended option — a minimal single-page Q&A-and-citations interface is directly demoable as a product, which matters given the project's explicit goal of showing value as a product rather than demonstrating AI tooling in the abstract. A real API underneath keeps a CLI or other client cheap to add later rather than requiring a rebuild.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Service Topology

**Decision**: One live service for v1 (the Advisor Service, behind the web app's API). Corpus Ingestion is a Corpus Curator-run script/tool, not a deployed service — it writes into the same Corpus Store the Advisor Service reads from, but nothing keeps it running.

**Why**: No genuine driver for a second service exists yet, the way HiveSight's async image-analysis pipeline earned its Analysis Service split. Ingestion is an offline, curator-triggered batch operation with no user-facing path and nothing time-sensitive. Follows `sdlc-architecture-codebase-design`'s rule directly: don't introduce a seam, let alone a service, until there are two real adapters or a clear near-term second one. Revisit if ingestion needs to run on a schedule against live sources rather than on demand.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Generation And Embedding Providers

**Decision**: Claude for generation, Voyage AI for embeddings.

**Why**: Confirmed. On generation, v1's actual requirements (never blend jurisdictions into one claim, never answer ungrounded without saying so, always cite) are fundamentally instruction-following and citation-discipline requirements, which is the kind of constraint-adherence task worth choosing a model for deliberately. On embeddings, Anthropic has no first-party embeddings API and explicitly recommends Voyage AI (now part of MongoDB) as its embeddings partner, with `voyage-3-large` as the current recommended model — confirmed via search rather than assumed, given the fast-moving provider landscape.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Database Technology

**Decision**: One Postgres database with the `pgvector` extension, covering both the Advisor Data Store and the Corpus Store (including Passage embeddings).

**Why**: Confirmed. V1 corpus is small enough that a dedicated vector database is infrastructure for a problem that doesn't exist yet; `pgvector` is mature at this scale. One database keeps backup, local dev, and any cross-store transaction needs simple. Also happens to match HiveSight's own stack, which costs nothing extra to learn even though the two products remain architecturally independent.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Jurisdiction Resolution

**Decision**: Explicit, required selection in the UI before a Query can be submitted — a simple US/UK toggle for v1. No inference from Query text, no Workspace-level default preference yet.

**Why**: Confirmed. Inferring jurisdiction from free text is an NLP reliability problem not worth taking on for a two-option set; explicit selection makes FR-003's non-blending guarantee trivial since Jurisdiction is known before retrieval runs, not guessed at afterward. A Workspace-level default is a cheap enhancement to add once reselecting every query is actually annoying in practice — not worth building ahead of that pain for a population of one.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Ingestion Trigger (Corollary, Not A Fresh Question)

**Decision**: Corpus Document ingestion and re-ingestion is manual, Corpus Curator-triggered, on demand.

**Why**: Follows directly from the Service Topology decision — ingestion is a curator-run script, not a live scheduled service, and no async driver was found to justify one. Recorded explicitly rather than left implicit, but not put to a fresh grilling question since the answer was already determined by an earlier decision.

## 2026-07-31 Source Supersession And Conflict Detection

**Decision**: Manual Corpus Curator judgement, at ingestion time, for both Source Supersession and Source Conflict detection. No automated freshness re-crawling or contradiction detection in v1.

**Why**: Confirmed. Corpus is small enough that hand-checking both at the moment a document is added or updated is genuinely cheap, and it's the same moment the Curator is already looking closely at the document. Ingestion-time detection also avoids expensive cross-document comparison on every Query. Same "don't automate ahead of the pain" reasoning as Service Topology, Jurisdiction Resolution, and Database Technology.

**Resolved via**: grilling session with Claude.

## 2026-07-31 Retention And Deletion Planning

**Decision**: The actual retention/deletion policy for Query, Answer, Citation, and Correction history remains deferred — no v1 UI, no enforcement, no scheduled purge. But the domain model is proactively updated now, not left as a bare "TBD": a dormant `Data Deletion Request` entity is added to `architecture/domain-model.md`, reserved and not reachable by any v1 workflow, with the same five statuses as HiveSight's own `Data Deletion Request` entity (`requested`, `in_review`, `completed`, `rejected`, `partially_completed`) for consistency across both products.

**Why**: The user's explicit instruction — deferring the policy decision is fine, but "at least plan for it, because from the past trying to retroactively fit compliance to these sorts of policies can be a problem." Workspace-scoping already gives the future entity a clean unit of deletion for free: `Query`, `Answer`, `Citation`, and `Correction` are all Workspace-owned, while `Corpus Document` and `Passage` are not, so a future Workspace deletion will never need to touch shared corpus content. This mirrors the same "build the schema now, activate the workflow later" pattern already used for `Correction`'s dormant `review_*` states, and parallels HiveSight's own still-deferred deletion gap rather than inventing a new pattern.

A second, distinct point is flagged rather than solved: local deletion is necessary but not sufficient. Query text sent to Voyage AI (embeddings) and Claude (generation) may be retained on their side under their own data-retention terms, independent of anything deleted locally. Confirming and, where available, configuring zero/short retention with both providers is real integration work that must happen before a future deletion workflow can be considered complete — it is a separate task from building the `Data Deletion Request` workflow itself, not a detail folded silently inside it.

**Resolved via**: grilling session with Claude, in response to explicit user instruction to plan ahead for compliance rather than defer it entirely.

## 2026-07-31 Deployment Platform

**Decision**: Fly.io hosts the first production-like environment — both the Advisor Service and the Postgres/`pgvector` database.

**Why**: V1 is one service and one small database with no scaling problem to solve yet, so a managed platform beats AWS/GCP on setup and ongoing ops time at this scale, at comparable dollar cost. Confirmed after a cost comparison: Fly and Render land in a similar $15–25/month range for this workload; AWS/GCP would be a similar dollar cost but with materially more setup and maintenance overhead (VPC, IAM, security groups) for a solo-maintained project. Fly's own Postgres pricing only jumps sharply at a 3-node production cluster tier, which is well beyond v1's actual need. LLM/embedding provider costs (Claude, Voyage AI) are usage-based and tracked separately from hosting, not a factor in this platform choice.

**Resolved via**: grilling session with Claude, including a dedicated cost-implications pass before confirming.

## 2026-07-31 Slice 0001 Test And Seed Approach

**Decision**: For Vertical Slice 0001 (Grounded Query Answer With Seeded Corpus): the Claude generation call is stubbed behind a documented fixture in the default automated test suite, not called for real on every run; a real call is exercised manually, or via a separate live test not run on every commit, before the slice is considered done. The hand-seeded Passage is created via a checked-in, rerunnable seed script, not a one-off manual insert.

**Why**: A real Claude call in every automated test run adds cost and flakiness unrelated to whether the code is correct — the thing worth testing automatically is that the right grounding context is sent and the response is parsed correctly, not whether the provider is reachable today. Mirrors the dependency-injection convention (`sdlc-delivery-dependency-injection`) of stubbing external adapters in the default test run. A checked-in seed script is reusable for slice 2 (a second jurisdiction, needed to actually prove FR-003), rather than redoing manual setup by hand each time.

**Resolved via**: grilling session with Claude, during vertical slice planning for Slice 0001.
