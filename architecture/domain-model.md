# Domain Model

## Purpose

This document defines the HiveSight Advisor domain model in technology-neutral terms. It should guide architecture, schema design, API design, acceptance tests, and traceability without choosing a framework, database, vector store, or model provider.

The canonical project vocabulary lives in `CONTEXT.md`. That glossary explicitly reuses HiveSight's terms where the underlying concept is genuinely the same, reworks a few where the subject matter differs, and deliberately does not import HiveSight's model-training lifecycle vocabulary, which does not apply to a retrieval-and-generation product. This document follows the same alignment discipline: it does not contradict HiveSight's domain model, and it says so explicitly at each point of overlap rather than leaving the reader to infer it.

A visual version of the model is maintained in `architecture/domain-model-diagram.md`.

## Scope

Version one is Phase 1 only: a grounded knowledge assistant. Phase 2 (the Advisor's action-proposing capability) is out of scope for this document except where a concept must be named now to avoid overbuilding a wrong shape later.

In scope:

- workspace-owned queries, answers, corrections, and jurisdiction preferences
- registered user with a default workspace and owner workspace membership, matching HiveSight's pattern
- beekeeper as the primary product persona
- a curated, multi-jurisdiction corpus (US and UK for v1) of licensed source documents
- retrieval-grounded answer generation with mandatory citation
- jurisdiction disambiguation and non-blending of cross-jurisdiction guidance
- source freshness (supersession) and source conflict surfacing
- a correction mechanism that captures evaluation evidence
- corpus document provenance and licence tracking

Out of scope for v1 (see `requirements/requirements.md` for the full list and reasoning):

- Phase 2 treatment plan drafting and treatment record-keeping
- any HiveSight data integration
- EU jurisdiction coverage beyond the deferred, member-state-granular future expansion
- a review-decision gate on corrections (the concept is modelled but dormant; see below)
- multi-user collaboration in practice, even though the domain shape supports it (matches HiveSight's own v1 posture)

## Core Entities

### Workspace

The ownership boundary for this product's data, matching HiveSight's Workspace concept exactly in shape, differing in what it owns.

Essential fields:

- id
- display name
- status
- created at

Relationships:

- has many workspace memberships
- owns many queries, answers, corrections, and jurisdiction preferences

Notes:

- One default workspace is created per user, matching HiveSight's registration-time pattern.
- Does not own Corpus Documents or Passages — those are shared, workspace-independent product content, not per-tenant data.

### User

A registered login identity. Defined identically to HiveSight's `CONTEXT.md`; see there for the canonical definition. Not redefined here.

### Workspace Membership

The relationship granting a User access to a Workspace with a role. Defined identically to HiveSight's `CONTEXT.md`.

Version-one roles:

- `owner`

Future roles are not yet named; HiveSight's own `member`/`inspector`/`advisor`/`reviewer` set is not assumed to transfer directly, since this product's collaboration shape has not been designed yet.

### Internal Capability

An authorization grant separate from ordinary Workspace Membership. Defined identically to HiveSight's `CONTEXT.md` in shape.

Version-one capabilities:

- `corpus_curator`

### Corpus Curator

The internal actor/persona for corpus governance work — adding, retiring, or flagging Corpus Documents.

Notes:

- Not a separate login identity; a User with the `corpus_curator` internal capability, exactly parallel to HiveSight's Dataset Curator.
- In practice, for the foreseeable future, this is the same person as the Beekeeper persona (see `requirements/decision-log.md`, Correction Trust Level For V1, for the reasoning behind why that matters for trust decisions elsewhere in this model).

### Beekeeper

The product persona for a person asking questions and reviewing answers.

Notes:

- Not a persisted entity, matching HiveSight's treatment of Beekeeper as an actor/persona rather than a stored record.
- In version one, the registered User with the owner Workspace Membership acts as the primary Beekeeper.

### Jurisdiction

The regulatory/guidance context that determines which treatments and guidance are applicable to a Query.

Essential fields:

- id
- code (for example, `us`, `uk`)
- display name
- status

Version-one values:

- `us`
- `uk`

Rules:

- EU is explicitly deferred and, when added, must be modelled at member-state granularity (`fr`, `de`, and so on), not as a single `eu` value — confirmed via grilling, see `requirements/decision-log.md`, V1 Jurisdiction Scope.
- Every Corpus Document belongs to exactly one Jurisdiction.
- An Answer must not present Passages from more than one Jurisdiction as a single undifferentiated response.

### Corpus Document

A single ingested source document.

Essential fields:

- id
- title
- jurisdiction id
- source organisation
- source url or reference
- licence terms
- retrieved/version date
- status
- superseded by corpus document id (nullable)
- created at

Statuses:

- `active`
- `superseded`
- `retired`

Rules:

- Every Corpus Document carries licence terms explicitly (NFR-003) — this is not optional metadata, because corpus sources carry materially different reuse terms (for example, the HBHC guide's CC BY-NC-ND terms versus PMC's more permissive open-access licences).
- A `superseded` Corpus Document remains citable for historical/audit purposes but must never be presented to a Beekeeper as current guidance (FR-005).
- Source Supersession is a relationship on this entity (`superseded_by_corpus_document_id`), not a separate join table, because it is always one-to-one at any point in time.

### Passage

A retrievable chunk of text within a Corpus Document.

Essential fields:

- id
- corpus document id
- text content
- position/offset within the source document
- embedding reference

Relationships:

- belongs to exactly one Corpus Document
- may be cited by many Answers

Rules:

- A Passage inherits its Jurisdiction and licence terms from its Corpus Document; it does not carry its own copy of that metadata.

### Query

A Beekeeper's natural-language question.

Essential fields:

- id
- workspace id
- created by user id
- text
- resolved jurisdiction id (nullable until resolved)
- created at

Relationships:

- belongs to one Workspace
- has one Answer (version one: one Query produces one Answer; follow-up questions are new Queries, not a thread, until conversational history is explicitly designed)

### Answer

The system's response to a Query.

Essential fields:

- id
- query id
- grounding status
- generated text
- answer generation version id
- created at

Grounding statuses:

- `grounded`
- `partial` (adjacent Passages offered, no direct match)
- `ungrounded` (no relevant Passages; system states this explicitly rather than answering from unsourced general knowledge)

Relationships:

- belongs to one Query
- has many Citations
- was produced by one Answer Generation Version
- may have many Corrections
- may have many Source Conflict flags

Rules:

- An Answer with grounding status `grounded` or `partial` must have at least one Citation. An Answer with status `ungrounded` must have zero Citations and must say so explicitly in its generated text (FR-008).
- An Answer must never claim to be grounded while citing Passages from more than one Jurisdiction as if they were in agreement, unless the generated text explicitly attributes each claim to its Jurisdiction (FR-003).

### Citation

The recorded link between an Answer and a Passage.

Essential fields:

- id
- answer id
- passage id
- corpus document id (denormalised for convenience; must match the passage's parent)

Relationships:

- belongs to one Answer
- references one Passage

### Source Conflict

A recorded instance where two or more Corpus Documents materially disagree on guidance relevant to a Query.

Essential fields:

- id
- answer id
- conflicting corpus document ids
- description
- created at

Rules:

- A Source Conflict is surfaced to the Beekeeper explicitly within the Answer, not silently resolved by picking one source (FR-006).
- Recording a Source Conflict does not imply either source is wrong; both may be correctly citable within their own Jurisdiction or as of their own version date.

### Correction

A Beekeeper flag that an Answer is wrong or misleading.

Essential fields:

- id
- workspace id
- answer id
- created by user id
- notes
- status
- created at

Version-one statuses:

- `submitted`
- `trusted` (applied directly as evaluation evidence; version one's only real terminal state)

Reserved, not yet exercised:

- `review_pending`
- `review_approved`
- `review_rejected`

Rules:

- Every Correction is workspace-scoped, matching HiveSight's ownership pattern.
- In version one, every Correction transitions directly to `trusted` with no human review gate — confirmed via grilling, see `requirements/decision-log.md`, Correction Trust Level For V1. The `review_*` statuses are modelled now, exactly parallel to HiveSight's Review Decision concept, so activating a review gate later is a status-transition change, not a schema change.
- A Correction is evaluation evidence, not automatically a corpus edit. It does not itself change a Corpus Document or Passage.

### Data Deletion Request

A request to delete or purge workspace-held data (Query, Answer, Citation, Correction history). Reserved now, not operational in v1 — confirmed via grilling, see `requirements/decision-log.md`, Retention And Deletion Planning.

Essential fields:

- id
- workspace id
- requester id
- status
- requested at
- completed at
- notes

Statuses (matching HiveSight's `Data Deletion Request` exactly, for consistency):

- `requested`
- `in_review`
- `completed`
- `rejected`
- `partially_completed`

Rules:

- The operational workflow is deferred, exactly parallel to HiveSight's own deferred deletion gap — no UI, no enforcement, no scheduled purge in v1.
- The entity exists now specifically so that adding a real deletion workflow later is implementation work, not a retroactive schema and product redesign. Retrofitting compliance onto a system not built to support it is expensive; this is the cheap insurance against that.
- Workspace-scoping already gives this entity a clean unit of deletion: Query, Answer, Citation, and Correction are all Workspace-owned, while Corpus Document and Passage are not (see the Corpus Document / Passage entities above) — so a future Workspace deletion never needs to touch shared corpus content, only that Workspace's own interaction history.
- Deleting internal records is necessary but not sufficient. Query text sent to the embedding and generation providers (Voyage AI, Claude) may be retained on their side under their own data-retention terms, independent of anything deleted here. Confirming and, where available, configuring zero/short retention with both providers is real integration work that must happen before this entity's workflow can be considered complete — it is not satisfied by deleting local rows alone.

### Answer Generation Version

A named version of the retrieval-and-generation configuration that produced a set of Answers.

Essential fields:

- id
- embedding model identifier
- generation model identifier
- prompt template version
- corpus snapshot reference
- created at

Relationships:

- produced many Answers

Rules:

- Every Answer records the Answer Generation Version that produced it, exactly parallel to HiveSight's invariant that every Analysis Result records its Model Version — for the same reason: without this, a bad Answer cannot be traced back to whether it was a retrieval problem, a generation problem, or a stale corpus snapshot.
- This is not a trained model version. There is no Training Run, Dataset Version, or Benchmark Evaluation in this product's v1 — see `CONTEXT.md`, "Terms Deliberately Not Imported (Yet)".

## Relationship Summary

- Workspace has many Workspace Memberships.
- Workspace owns many Queries, Answers (through Queries), and Corrections.
- User has many Workspace Memberships and may have many Internal Capabilities.
- Workspace Membership belongs to one User and one Workspace.
- Internal Capability belongs to one User.
- Jurisdiction has many Corpus Documents.
- Corpus Document has many Passages.
- Corpus Document may be superseded by one other Corpus Document.
- Query belongs to one Workspace and has one Answer.
- Answer belongs to one Query, has many Citations, was produced by one Answer Generation Version, may have many Corrections, and may have many Source Conflict flags.
- Citation belongs to one Answer and references one Passage.
- Correction belongs to one Answer and one Workspace.
- Data Deletion Request belongs to one Workspace.

## Lifecycle States

### Corpus Document

- `active`
- `superseded`
- `retired`

### Answer

Grounding status is set once at creation and does not transition (a new Query produces a new Answer rather than mutating an old one):

- `grounded`
- `partial`
- `ungrounded`

### Correction

- `submitted`
- `trusted` (v1 terminal state)
- `review_pending` (reserved, not exercised in v1)
- `review_approved` (reserved)
- `review_rejected` (reserved)

### Data Deletion Request

Reserved, not reachable by any v1 workflow:

- `requested`
- `in_review`
- `completed`
- `rejected`
- `partially_completed`

## Invariants

- Every Workspace Membership belongs to exactly one User and one Workspace.
- Every Internal Capability belongs to exactly one User.
- Every Corpus Document belongs to exactly one Jurisdiction.
- Every Passage belongs to exactly one Corpus Document and inherits its Jurisdiction and licence terms.
- Every Query belongs to exactly one Workspace.
- Every Answer belongs to exactly one Query and records exactly one Answer Generation Version.
- An Answer with grounding status `grounded` or `partial` has at least one Citation; an Answer with status `ungrounded` has zero Citations.
- An Answer must not blend Passages from more than one Jurisdiction into an unattributed single claim.
- A `superseded` Corpus Document may still be cited but must never be presented as current.
- A Correction is evaluation evidence, never an automatic corpus or Passage edit.
- Every Correction belongs to exactly one Workspace and one Answer.
- V1 Corrections reach `trusted` directly; the `review_*` states exist in the model but are not reachable by any v1 workflow.

## Derived Values And Calculations

None in version one. Retrieval ranking scores are an implementation detail of the retrieval seam, not a domain-level derived value, and are deliberately not modelled here (see `architecture/system-context.md` for where that seam lives).

## Consent, Privacy, And Ownership Boundaries

Lighter than HiveSight's, because this product does not handle photos or biological specimen data, but not absent:

- Workspace remains the ownership boundary for Queries and Corrections, matching HiveSight's pattern, because a Query's free text may incidentally contain personal or location information about a Beekeeper's own apiary.
- Every Corpus Document's licence terms must be respected by the retrieval and generation pipeline — for example, the HBHC guide's CC BY-NC-ND terms constrain reuse and redistribution even though the guide itself is freely readable.
- Query text sent to an external generation or embedding provider crosses a real trust boundary (see `architecture/system-context.md`) and should be treated with the same seriousness HiveSight applies to photo data leaving its boundary, even though the sensitivity profile is lower.
- A `Data Deletion Request` entity is reserved in the model now (see the Correction section above) precisely so that a future retention/deletion policy is implementation work against an existing shape, not a redesign — confirmed via grilling, see `requirements/decision-log.md`, Retention And Deletion Planning.

Deferred (the policy decision, not the design readiness for it):

- The actual retention/deletion policy for Query/Answer/Correction history — what triggers deletion, what time limits apply, what "purged" means operationally — is not decided, parallel to HiveSight's own deferred Data Deletion Request gap.
- Whether and how third-party provider retention (Voyage AI, Claude) needs to be configured before a real deletion workflow can be considered complete. Deleting local rows does not by itself satisfy a deletion request if a provider retains the underlying Query text on their own terms.

## Model And Dataset Governance Concepts

This product has no trained model in v1 — see `CONTEXT.md`, "Terms Deliberately Not Imported (Yet)". The governance concepts that do apply, mapped against the checklist in `sdlc-architecture-domain-model`:

- **Model version equivalent**: Answer Generation Version, above.
- **Dataset version / benchmark evaluation equivalent**: not yet modelled. FR-007 anticipates Corrections becoming evaluation evidence; if a formal benchmark question/answer set is built later, it should get its own lightweight entity at that time rather than borrowing HiveSight's heavier Dataset Version/Training Run/Benchmark Evaluation shape prematurely.
- **User correction**: Correction, above.
- **Review decision**: reserved but dormant, folded into Correction's status enum rather than modelled as a separate entity, since v1 has no other subject that would need reviewing.
- **Consent record**: no discrete entity in v1; corpus licensing is tracked on Corpus Document, and Workspace Data Use Agreement-style consent has not been judged necessary yet since there is no personal biological/photo data collection — revisit if Query/Answer retention policy decisions change this.

## Traceability

- `Workspace`, `User`, `Workspace Membership` support the foundational multi-user modelling decision (FR-000).
- `Query`, `Answer`, `Citation` support FR-001 and FR-002.
- `Jurisdiction` and the cross-jurisdiction invariant on `Answer` support FR-003.
- `Corpus Document` (status/supersession) supports FR-005.
- `Source Conflict` supports FR-006.
- `Correction` supports FR-007.
- `Answer` grounding status supports FR-008.
- `Corpus Document` licence terms support NFR-003.
- Absence of a HiveSight foreign key anywhere in this model supports NFR-004.
- `Data Deletion Request` supports the retention/deletion planning decision (deferred policy, planned-for schema). See `requirements/decision-log.md`, Retention And Deletion Planning.

## Open Architecture Questions

- ~~What is the primary application surface for v1...~~ — resolved: web app, backed by a real API. See `requirements/decision-log.md`, V1 Application Surface.
- ~~Should the Advisor Service and Corpus Ingestion be separate...~~ — resolved: one live service, ingestion is a curator-run script. See `requirements/decision-log.md`, Service Topology.
- ~~What embedding model and generation model/provider should power v1...~~ — resolved: Claude for generation, Voyage AI for embeddings. See `requirements/decision-log.md`, Generation And Embedding Providers.
- ~~How is a Query's Jurisdiction resolved...~~ — resolved: explicit, required UI selection. See `requirements/decision-log.md`, Jurisdiction Resolution.
- ~~What triggers Corpus Document ingestion...~~ — resolved: manual, Corpus Curator-triggered, on demand. See `requirements/decision-log.md`, Ingestion Trigger.
- ~~How is Source Supersession detected...~~ / ~~How is a Source Conflict detected...~~ — resolved: manual Corpus Curator judgement at ingestion time, for both. See `requirements/decision-log.md`, Source Supersession And Conflict Detection.
- ~~What is the retention/deletion policy for Query, Answer, and Correction history?~~ — planned for, not decided: the policy itself remains deferred, but a dormant `Data Deletion Request` entity is now in the model so implementing it later is not a schema redesign. See `requirements/decision-log.md`, Retention And Deletion Planning.
