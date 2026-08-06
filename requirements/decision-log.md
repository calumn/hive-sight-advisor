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

**Addendum, 2026-08-03 — verified provider terms, not just flagged as unknown**: Checked Anthropic's and Voyage AI's actual current commercial terms rather than leaving this as an open question. Anthropic's API (a commercial product, distinct from consumer Claude) is not trained on by default, with a 30-day retention window for abuse/safety monitoring unless a Zero Data Retention (ZDR) enterprise agreement is arranged, which removes even that. Voyage AI's default differs meaningfully: free-tier data is used for training by default; paid-tier customers can opt into zero-day retention, but it requires an active payment method and org-admin action, not an automatic entitlement. This project's Voyage usage has repeatedly hit the free-tier rate-limit error ("you have not yet added your payment method") throughout this session, confirming it is currently running on the free tier — meaning corpus/query text sent to Voyage so far may be usable for their training under current terms. This is a verified, concrete finding, not a hypothetical: closing it means moving to a paid Voyage plan with the training opt-out explicitly enabled, which is real, unstarted work distinct from anything else in this decision.

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

## 2026-08-03 Corpus Curator CLI Tooling And AI-Assisted Review

**Decision**: Seven resolutions, covering both the AI-assisted review step (raised by the user mid-scoping) and the CLI tool's own shape:

1. The review step checks topic/jurisdiction relevance and potential overlap or contradiction with existing corpus content — not factual/scientific accuracy of treatment claims.
2. The review is advisory only, never a blocking gate; the Curator's confirmation is what decides whether a document is added.
3. The review compares the candidate document against the nearest existing Passages in the same Jurisdiction (via the existing `CorpusRepository`), not just the candidate in isolation.
4. This is a local CLI script with direct database/API-key access, not new HTTP admin endpoints.
5. The tool persists what it adds/retires to a source-controlled data file, not the live database alone, so the corpus stays fully reproducible from a fresh clone.
6. That file is a separate structured YAML file the seed script loads, not an appended/rewritten Python dataclass in `seed_slice_0001.py`.
7. V1 covers add and retire only; updating an existing document or marking supersession via the tool are deferred, still reachable the existing way.

**Why**: The review step's scope (1–3) keeps the tool in its lane — an LLM judging specialized apiculture/veterinary accuracy would be a false authority, but relevance-and-overlap-against-what's-already-there is a concrete, checkable signal, and reuses retrieval infrastructure that already exists. Advisory-only matches the same reasoning as Correction Trust Level For V1: one real curator, who is also the domain expert, makes a hard gate just self-review with extra steps. A CLI script (4) avoids inventing a corpus-admin access-control model that doesn't otherwise exist — the dev-header only identifies a user for workspace-membership checks, nothing about corpus-mutation permission. Persisting to source control (5–6) protects a property this project has treated as non-negotiable everywhere else (checked-in migrations, a rerunnable seed script) — quietly losing it for curator-added content would be a real regression; a separate YAML file avoids the fragility of a CLI tool programmatically rewriting Python source. Scoping to add/retire only (7) matches exactly what was asked for; update and mark-superseded are smaller mechanical extensions better built once this tool's shape has proven itself.

**Resolved via**: grilling session with Claude, seven questions in sequence (three raised by the user mid-scoping about the review step, four about the tool's own shape), during vertical slice planning for Slice 0006.

## 2026-08-03 Treatment Trade-Off Comparison Mechanism

**Decision**: Five resolutions covering FR-004's mechanism:

1. Trade-off attributes (temperature constraints, organic-certification compatibility, treatment duration) stay as prose within Passage text, not structured columns on Corpus Document.
2. Retrieval always widens (retrieves several closest Passages, not just one) for every Query — no intent detection to decide when to "turn on" comparison mode.
3. The workflow retrieves up to 5 Passages per Query (a small fixed number, not "all Passages in the jurisdiction").
4. `grounding_status` remains based purely on the single closest Passage's distance, unaffected by how many Passages were retrieved or cited.
5. No new UI structure (e.g. a trade-off table) — the existing prose-answer-plus-citations-list rendering is unchanged.

**Why**: Prose-only (1) is already proven to work — a live query against the real corpus produced an accurate, well-organized comparison purely from prose with no structured extraction, and a structured schema is real, speculative complexity (new columns, curator data-entry burden, migration work) for a need that hasn't shown up yet. Always-widening retrieval (2) avoids building a fragile "is this a comparison question" classifier for something the retrieval-plus-prompt combination can already handle naturally: a single genuinely relevant Passage still produces a single answer, several relevant ones produce a comparison, without a separate code path. A small fixed retrieval width (3) covers every document in both jurisdictions today while remaining genuine top-N behaviour that keeps working sensibly as the corpus grows, rather than a stopgap that needs revisiting at the next added document. Keeping grounding independent of comparison (4) avoids conflating two different questions — "how well-matched is the best source" versus "how many relevant options exist" — the same reasoning already used for the superseded-source flag in Slice 0004; a comparison across three so-so matches shouldn't be penalised as `partial`, and an excellent single match shouldn't be forced into an unnecessary comparison. No UI change (5) follows directly from the existing citations list already supporting multiple entries since Slices 0004–0005.

**Resolved via**: grilling session with Claude, five questions in sequence, during vertical slice planning for Slice 0007.

## 2026-08-05 Agentic Treatment Plan Request Mechanism

**Decision**: Six resolutions, covering FR-009's first slice (Slice 0008) — the first agentic behaviour and first cross-application integration point in this codebase:

1. Hive identity is HiveSight's alone. The Advisor treats a hive ID as an opaque foreign identifier and does not model Hive as its own domain entity.
2. HiveSight's two endpoints (accept-suggestion, completion webhook) do not exist yet and are not built here. This slice builds only the Advisor's inbound endpoint plus a stub `TreatmentSuggestionProvider` adapter standing in for HiveSight's outbound acceptance, and a test-only endpoint standing in for HiveSight's future completion webhook.
3. The workflow is a LangGraph graph (`Recommend` → `Suggest` → `Wait` → `Resume`), not a hand-rolled loop — a deliberate first use of an agent-orchestration library in this codebase, chosen both to demonstrate agentic-AI concepts genuinely (as opposed to a single-pass tool call) and because a known prospect uses LangChain/LangGraph.
4. The graph's suspend must be backed by a real, Postgres-backed LangGraph checkpointer, not an in-memory one — an in-memory suspend would look identical in a demo but prove nothing about durability, which is the entire point of the `Wait` step.
5. Service-to-service authentication uses a shared-secret header (e.g. `X-HiveSight-Service-Key`), checked via a dedicated FastAPI dependency wired only to a new `/integrations/hivesight/*` router — never to Beekeeper-facing or Corpus Curator routes. OAuth2 client-credentials is named as the deliberate future upgrade if this ever needs to support more than one external caller or expiring credentials; it is not built now.
6. This inbound call requires no Beekeeper login/Workspace context — it is app-to-app, authenticated purely via the service credential above.

**Why**: Hive identity (1) closes an open roadmap question in the same spirit as the earlier system-of-record split — duplicating a Hive entity in this codebase would create exactly the kind of two-systems-of-record problem that split was meant to avoid. Building only the Advisor's side against stubs (2) follows the same Protocol/stub/live adapter pattern used everywhere else in this codebase (`EmbeddingProvider`, `GenerationProvider`, `CorpusReviewProvider`) — HiveSight's real endpoints are the other project's build, tracked on its own roadmap, not a blocker to demonstrating this side. LangGraph (3) is a genuine, not cosmetic, choice: this is the first workflow in the project that must survive a suspend across an indefinite real-world wait (days or weeks until a beekeeper acts in HiveSight), which is precisely the class of problem LangGraph's checkpointing exists for, and it doubles as hands-on fluency with a tool relevant to a live business conversation. A real Postgres-backed checkpointer (4) is non-negotiable for the same reason — this project already uses "prove it don't assume it" as a working method (see the live acceptance pass's threshold-drift finding), and an in-memory stand-in would be exactly the kind of demonstration that looks convincing but proves nothing. A shared-secret header scoped by router wiring (5) matches this project's consistent pattern of building the lightest defensible mechanism first (dev-header user auth, a simple equality check for corpus curation) rather than standing up enterprise auth infrastructure for what is currently one known caller — the scoping is structural (which dependency a router uses), not encoded in the credential, since a static secret carries no claims to scope by. No Beekeeper context on the inbound call (6) follows directly from this being app-to-app, not a Beekeeper session — conflating the two auth models would blur a distinction worth keeping sharp.

**Resolved via**: grilling session with Claude, six questions in sequence plus one follow-up question on the auth pattern specifically, during vertical slice planning for Slice 0008.

## 2026-08-05 Reject-And-Revise Treatment Plan Mechanism

**Decision**: Six resolutions, covering Slice 0009 — the first genuinely cyclical graph in this codebase (Slice 0008's graph was a DAG plus one interrupt, not a loop):

1. The rejection trigger mirrors Slice 0008's completion-confirmation endpoint exactly: a test-only `POST /integrations/hivesight/treatment-plans/rejections`, body `{hive_id, reason}`, standing in for HiveSight's not-yet-built rejection webhook.
2. The rejection reason feeds the next `Recommend` call by being appended as extra context to the original query text — `AnswerQueryWorkflow`'s own interface is untouched; the loop is entirely the graph's concern, not the wrapped RAG pipeline's.
3. The loop is capped at 3 revisions (`MAX_REVISIONS`), tracked as a counter in graph state — an explicit judgment call, not a calibrated number, chosen only to guarantee termination.
4. When the cap is reached, the graph stops looping and returns its last answer with an explicit `revision_exhausted: true` flag, rather than silently behaving as if still awaiting a normal response — so the caller can distinguish "still pending" from "we ran out of alternatives."
5. Each revision is persisted as a **new** `proposed_treatments` row (status `suggested`) with a `supersedes_proposed_treatment_id` pointer to the row it replaces, whose own status becomes `rejected` — never an in-place mutation of the rejected row's content.
6. Each revision re-triggers the `Suggest` step (the stub `TreatmentSuggestionProvider` is called again), since in the real world a revised suggestion is new information HiveSight needs to receive, not an edit to something it already has.

**Why**: Mirroring the existing completion endpoint (1) keeps the two HiveSight-facing stand-in endpoints symmetric and avoids inventing a second shape for what is structurally the same kind of external signal. Appending the reason as query-text context (2) avoids widening `AnswerQueryWorkflow`'s interface for a concern that belongs to the agentic wrapper, not the underlying grounded-answer pipeline every other slice already depends on. A capped loop (3, 4) is the direct consequence of introducing a real cycle — an uncapped loop risks never terminating if a caller (or eventually a real beekeeper) simply keeps rejecting, and returning silently as "pending" once exhausted would hide a real dead end behind a state that looks identical to "still waiting," which is worse than an explicit flag. The append-only persistence model (5) follows the precedent already set twice in this codebase — Corrections (multiple allowed per Answer, never overwritten) and Source Supersession (a new document is pointed to, never mutated in place) — for the same underlying reason: preserving the full negotiation history costs little and this project has consistently chosen it over losing history to convenience. Re-triggering `Suggest` per revision (6) treats a revision as what it actually is from HiveSight's perspective — new information — rather than quietly assuming HiveSight will infer an update from a response it never explicitly sent.

**Resolved via**: grilling session with Claude, six questions in sequence, during vertical slice planning for Slice 0009.

**Follow-up (2026-08-05, pre-implementation "grill me" pass)**: Four further resolutions, refining points 3–4 above and closing a gap the original six questions missed:

7. Reaching the revision cap does not end the episode entirely — the last suggested treatment remains genuinely acceptable (`confirm_completed` still works on it afterwards). `revision_exhausted` only forecloses further *revision*, not acceptance of what's already on offer.
8. `MAX_REVISIONS = 3` means 3 *revisions* on top of the original suggestion (4 suggestions total, ever). The 4th rejection — rejecting the 3rd revision — is the one that triggers `revision_exhausted`.
9. Because point 7 requires the last suggestion's suspend to survive being told "no more revisions," the rejection endpoint must check the revision count by **reading** graph state (`get_state`) before deciding whether to genuinely resume the graph. Only a below-cap rejection actually calls `Command(resume=...)`; an at-cap rejection reads state and returns the exhausted response without touching the graph at all, since LangGraph's interrupt is a one-shot resume with no "un-pause."
10. A revision that itself comes back ungrounded is treated as its own outcome, not folded into `revision_exhausted` — no new `Proposed Treatment` is recorded (matching FR-008's existing honest-no-answer rule everywhere else in this codebase), and `revision_exhausted` is reported `false`, since revisions weren't used up, there simply wasn't a good answer this time.

**Why (follow-up)**: Point 7 avoids a real usability trap — without it, a beekeeper who rejects three times but would have accepted the third alternative on reflection would have no way back in, which is a worse outcome than just running out of new ideas. Point 8's semantics ("3 revisions," not "3 suggestions") is the more natural and more generous reading, and matters concretely because it's an exact off-by-one that changes what the "exhausted" test scenario actually needs to set up. Point 9 is the direct mechanical consequence of point 7, not an independent design choice — LangGraph's interrupt/resume model has no way to "resume and then re-suspend at the same point," so preserving the suspend requires never resuming it in the exhausted case. Point 10 keeps a case out of `revision_exhausted` that has a different meaning entirely — conflating "we tried and found nothing" with "you've used up your chances" would hide a real gap (a rejected treatment with no successor of any kind) behind a flag that means something else.

**Resolved via**: follow-up grilling session with Claude (`productivity-grilling` skill), four questions in sequence, immediately before implementation of Slice 0009.

## 2026-08-05 Voyage Retry With Backoff Mechanism

**Decision**: Five resolutions, covering Slice 0010 — closing the "Handle Voyage AI's free-tier rate limits properly" roadmap item:

1. Retry-with-backoff is implemented at the adapter level (`VoyageEmbeddingProvider`), not as a LangGraph node or pattern, despite the recent run of agentic-AI slices — a graph-level retry would only protect the agentic `TreatmentPlanWorkflow`, leaving the plain web-UI query flow (the path that actually hit rate limits during threshold calibration) exactly as exposed as before.
2. Only transient errors are retried (`RateLimitError`, `ServiceUnavailableError`, `Timeout`, `APIConnectionError`, `TryAgain`); genuinely non-retryable errors (`AuthenticationError`, `InvalidRequestError`, `MalformedRequestError`) propagate immediately, unchanged from today.
3. Up to 3 retries (4 attempts total), exponential backoff from 1 second doubling to a cap of 8 seconds, with jitter — via `tenacity`, not hand-rolled.
4. Scope is Voyage only for this slice; a matching `ClaudeGenerationProvider` retry is explicitly parked rather than bundled in, since no real problem has surfaced there yet.
5. The test seam is an injectable client parameter on `VoyageEmbeddingProvider`, following the same constructor-injection pattern already used throughout this codebase's adapters, with tenacity's wait overridable for near-zero delay in tests.

**Why**: Point 1 is the key decision — it would have been easy to fold this into the recent agentic-AI momentum as a third LangGraph pattern, but the roadmap item this closes is about a real problem hit on the plain query path, not the agentic one, and building it as a graph-level pattern would have solved the more interesting problem instead of the actual one. Point 2 avoids masking real configuration/request errors behind a multi-second retry delay that can't possibly help them succeed. Point 3's numbers are a standard, defensible shape for this class of problem, not calibrated against real Voyage rate-limit recovery times — reasonable to revisit if it proves too short or too long in practice. Point 4 matches this project's consistent pattern of fixing the problem that was actually hit rather than its speculative twin. Point 5 keeps this consistent with how every other external dependency in this codebase is already made testable, rather than inventing a new seam style for one adapter.

**Resolved via**: grilling session with Claude, five questions in sequence, during vertical slice planning for Slice 0010.

## 2026-08-06 Treatment Plan Readiness Mechanism

**Decision**: Four resolutions, covering Slice 0011 — closing four Advisor-side contract gaps found while reviewing HiveSight's Slice 0029 and Slice 0029.5 designs:

1. `jurisdiction_id` (an internal Advisor UUID) is removed from the treatment-plans request and replaced with `jurisdiction_code` (e.g. `"uk"`/`"us"`), resolved to the internal UUID via a new `JurisdictionRepository` at the API boundary only — `AnswerQueryWorkflow`, `CorpusRepository`, and `TreatmentPlanState` keep using the internal UUID unchanged. This is a clean breaking change, not an additive/compatibility-preserving one, made now because no real caller exists yet.
2. `contract_version` is a single shared constant (`"treatment_plan_v1"`) applied to all three response shapes on the `/integrations/hivesight/*` router, not versioned independently per endpoint.
3. `answer_id` is exposed on all three responses, including the completion response (which carries no answer text/citations but already stores `answer_id` internally) — for full audit-correlation parity, not just the two that carry full answer content.
4. `request_treatment_plan` becomes idempotent per hive: it peeks at existing graph state before invoking anything (mirroring `reject_treatment`'s existing peek-before-resume pattern), and if a `proposed_treatment_id` is present, its *current* status is looked up via the repository — `suggested` short-circuits to the existing answer with no new graph run or row; `completed` (or `rejected`, the dangling reference an ungrounded revision can leave behind) proceeds with a genuinely fresh request. The short-circuited response is deliberately indistinguishable in shape from a fresh one — no added flag.

**Why**: Point 1 fixes a real integration-contract weakness identified during review — a raw internal primary key is not the kind of identifier that should cross a service boundary, and HiveSight would otherwise have had to hardcode Advisor's UUIDs out of band, silently breaking on reseed. Confining the fix to the API boundary avoids touching any of Advisor's internal, already-tested RAG plumbing. Point 2 treats the three treatment-plan endpoints as one integration surface that evolves together, avoiding premature independent versioning for endpoints that have never actually diverged. Point 3 costs nothing to extend to the completion response, since the data already exists internally, and audit correlation is exactly what HiveSight's own Slice 0029.5 design says it needs. Point 4 closes a genuine, empirically-verified bug (not a hypothetical): a second top-level request while the first sits unresolved silently orphaned it, because Advisor's LangGraph thread is keyed purely by `hive_id` with no other safeguard, and HiveSight's own Slice 0029.5 design guarantees this scenario will occur (it never calls Advisor's completion/rejection endpoints). The status check goes through the repository rather than graph-state fields alone because graph state can't reliably distinguish "still pending" from "fully completed" by itself — `last_action` looks the same (`None`) for a never-yet-resumed suggestion as it would need to for some other undecided cases, so trusting it directly would be fragile. No added flag on the short-circuited response, because HiveSight's own stated behaviour for its side of this exact case doesn't ask for one, and inventing a distinction nobody's asked to observe would be speculative complexity.

**Resolved via**: grilling session with Claude, four questions in sequence, during vertical slice planning for Slice 0011.
