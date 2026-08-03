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

## 2026-08-02 FR-008 Grounding Classification Mechanism

**Decision**: Grounding status (`grounded`/`partial`/`ungrounded`) is determined by a deterministic distance threshold on the top retrieved Passage's similarity score, not by asking the generation model to judge fit. Two thresholds classify the top match: close enough → `grounded`; somewhat related → `partial` (still cited, but the generated text is told explicitly this may not directly answer the question); too far, or no Passage exists for that Jurisdiction → `ungrounded`, which skips the generation call entirely and returns a canned message with zero Citations. The actual threshold values are provisional, calibrated by running a handful of real test queries (on-topic, borderline, and off-topic) against the two currently-seeded Passages, not from a proper calibration dataset. All three grounding states — not just `grounded`/`ungrounded` — are in scope for this slice, matching FR-008's explicit text and the domain model's already-modelled three-state shape.

**Why**: A deterministic threshold keeps grounding classification cheap, fully testable without a live Claude call, and consistent with this project's established bias toward avoiding live-call dependency in the default test suite. Skipping the generation call for the ungrounded case avoids paying for a call that has nothing to ground a nuanced answer in. Picking a provisional threshold now — rather than waiting for a "proper" calibration dataset — unblocks the slice, since the corpus only has two Passages total and there is no larger dataset to calibrate against yet anyway. Including `partial` now, rather than deferring it, costs nothing extra given the two-threshold mechanism naturally produces it, and deferring would leave FR-008 and the domain model's `grounding_status` shape only half-implemented.

**Resolved via**: grilling session with Claude, four questions in sequence (classification mechanism, ungrounded call-skipping, threshold calibration approach, partial-in-scope), during vertical slice planning for Slice 0003.

## 2026-08-03 Grounding Thresholds Are Environment-Configurable, Not a Single Hardcoded Value

**Decision**: `GROUNDED_DISTANCE_THRESHOLD` and `PARTIAL_DISTANCE_THRESHOLD` are read from `Settings` (`ADVISOR_API_GROUNDED_DISTANCE_THRESHOLD` / `ADVISOR_API_PARTIAL_DISTANCE_THRESHOLD` env vars), defaulting to the real-Voyage-calibrated 0.35/0.55, rather than staying module-level constants. The Playwright acceptance-test environment overrides these to stub-calibrated values (0.5/0.8) for its spawned API process only.

**Why**: Implementing Slice 0003's Playwright coverage surfaced that the stub `EmbeddingProvider`'s word-hashing distances sit on a fundamentally different scale than real Voyage embeddings — a query built almost entirely from the seeded Passage's own vocabulary only reached ~0.43 distance against it, and the existing Slice 0001/0002 "grounded" scenario's query scored 0.76, which would misclassify as `ungrounded` under the real-calibrated thresholds. This isn't a query-wording problem to work around; the two embedding schemes are not comparable in absolute distance, so one hardcoded threshold pair cannot serve both. Making the thresholds env-configurable keeps the calibrated real-world values as the actual production behaviour, isolates the fix to configuration rather than touching the stub's design or the workflow's logic, and preserves genuine end-to-end coverage of all three grounding states through the browser rather than dropping absolute-distance assertions from the acceptance suite.

**Resolved via**: discovered as a test failure while extending the Playwright + Gherkin suite for Slice 0003; user deferred the choice ("do whatever you think best") after being shown three options (env-configurable thresholds, a smarter stub embedding model, or dropping absolute-distance e2e assertions).

## 2026-08-03 Source Supersession Mechanism And Provenance Display

**Decision**: Six resolutions, covering FR-005 and NFR-003 together:

1. When the closest retrieved Passage belongs to a superseded Corpus Document, the system still retrieves and cites it — superseded documents are not excluded from the nearest-neighbor search. The Citation is instead clearly flagged as superseded (metadata only; the generation provider and its prompt are untouched) rather than presented as current.
2. The workflow does not chase down or cite the superseding document's own content this slice — flagging the outdated source is sufficient for v1.
3. The superseded signal lives on the Citation (a new field), not as a fourth `grounding_status` value — "is this well-matched" and "is this current" are independent questions, and `grounding_status` already carries a tested invariant unrelated to source currency.
4. Provenance and licence metadata (NFR-003) is attached to every Citation unconditionally, regardless of whether its source is superseded — NFR-003 is not conditioned on supersession.
5. The domain model's "retrieved/version date" field is not added as a new column; `corpus_documents.created_at` is treated as satisfying it for v1, since this corpus is manually curated and seeded once, so the two are the same instant for every document that exists today.
6. A new `source_url` column is added now (unlike the version-date field), with real reference URLs seeded for both existing documents.

**Why**: FR-005's own wording — "flag when a source it would otherwise cite has been superseded... rather than citing it as current" — only makes sense if citing it is still what happens, just not silently as current; excluding it from retrieval entirely would make the flagging behaviour unobservable and answer an easier requirement than the one written. Chasing the successor's content adds real complexity (it must cover the same topic at a similar passage granularity, which isn't guaranteed) for a case FR-005 doesn't actually ask for. Keeping the superseded flag off `grounding_status` avoids conflating two independent dimensions that the existing invariant (grounded/partial ⇒ ≥1 citation, ungrounded ⇒ 0) doesn't need to know about. NFR-003 has real licence-compliance weight (e.g. HBHC's CC BY-NC-ND terms require attribution whenever that content is shown, not just when it's outdated), so it applies unconditionally. `created_at` vs. a dedicated retrieved-date column, and `source_url`, were judged on different cost/value terms even though both are schema gaps versus the domain model: the date field would only earn its keep once a document can be updated in place without a status change (a case v1 doesn't have), while `source_url` is cheap and materially strengthens NFR-003's real intent — giving a Beekeeper somewhere to actually go to verify or attribute a licensed source.

**Resolved via**: grilling session with Claude, six questions in sequence, during vertical slice planning for Slice 0004.

## 2026-08-03 User Corrections Mechanism

**Decision**: Four resolutions, covering FR-007's mechanism (the trust-level question was already resolved separately — see Correction Trust Level For V1):

1. The "flag as wrong" control is available on every Answer regardless of `grounding_status`, including `ungrounded` — not restricted to grounded/partial answers.
2. Notes are required (non-empty); an unexplained flag cannot be submitted.
3. Multiple Corrections may be submitted for the same Answer — it is not a one-shot action, and the UI does not hide or disable the control after first use.
4. No structured "reason" taxonomy is added alongside notes for v1 — free-text only.

**Why**: The grounding thresholds are explicitly provisional (see FR-008 Grounding Classification Mechanism), so a Beekeeper disagreeing with an `ungrounded` classification is exactly the kind of evaluation evidence FR-007 exists to capture — excluding that state would silently cut off the most valuable feedback case. Requiring notes costs nothing and directly serves FR-007's framing of a Correction as "evaluation evidence," which an empty flag would barely qualify as. The domain model's `Correction` entity has no uniqueness constraint on `answer_id`, so allowing repeats avoids inventing a restriction the model doesn't ask for, and preserves a Beekeeper's ability to add detail later or a second person to flag independently. A reason taxonomy would add UI complexity and a schema field with no current reporting or consumption need — nothing yet reads or aggregates Corrections, so categorizing them now would be speculative.

**Resolved via**: grilling session with Claude, four questions in sequence, during vertical slice planning for Slice 0005.
