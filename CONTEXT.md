# HiveSight Advisor

HiveSight Advisor is a grounded knowledge and decision-support product for beekeepers managing Varroa mite risk. It is architecturally independent of HiveSight (confirmed via grilling, `requirements/decision-log.md`, 2026-07-31) but shares beekeeping domain territory with it, so this glossary deliberately reuses HiveSight's terms and definitions wherever the underlying concept is genuinely the same, and calls out explicitly where it diverges.

## Terms Reused From HiveSight, Unchanged

These are defined identically to HiveSight's `CONTEXT.md` because the underlying concept is the same. Do not redefine them here differently.

**User**:
A registered login identity that can authenticate and be authorized to act in one or more workspaces.
_Avoid_: Beekeeper when the point is login, registration, authentication, or identity.

**Workspace Membership**:
The relationship that gives a User access to a Workspace with a role.
_Avoid_: User ownership when the relationship between identity and workspace is meant.

**Internal Capability**:
An authorization grant separate from ordinary Workspace Membership, used for internal workflows such as corpus curation.
_Avoid_: Workspace role when the permission is not tied to ordinary Workspace access.

## Terms Reused From HiveSight, Reworded For This Product

Same concept and intent as HiveSight, but the definition text below is specific to this product because the underlying subject matter differs.

**Workspace**:
The ownership boundary for queries, answers, corrections, and jurisdiction preferences.
_Avoid_: Account when the ownership container, not login identity, is the point. (HiveSight's Workspace owns apiaries/hives/inspections; this product's Workspace owns knowledge-interaction history instead — same boundary concept, different owned entities.)

**Beekeeper**:
A beekeeping actor or persona who asks questions and reviews grounded answers. In version one, the registered User with the owner Workspace Membership acts as the primary Beekeeper.
_Avoid_: User when the point is knowledge-seeking work rather than login identity. (HiveSight's Beekeeper records inspections and reviews analysis results; this product's Beekeeper asks questions and reviews answers — same actor concept, different work.)

**Corpus Curator**:
A registered User with internal capability who can add, retire, or flag Corpus Documents.
_Avoid_: Beekeeper when the actor is doing internal corpus governance work. (Directly parallels HiveSight's Dataset Curator — a User with an internal capability distinct from ordinary Workspace Membership, not a separate login identity.)

**Correction**:
A Beekeeper flag that marks an Answer as wrong or misleading.
_Avoid_: Ground truth, training label. (Parallels HiveSight's User Correction — a flag on AI output, not authoritative by itself — but the subject here is a generated Answer, not a model Annotation.)

## Terms Specific To This Product

**Jurisdiction**:
The national or regional regulatory and guidance context (at minimum, in version one: US, UK) that determines which treatments and guidance are applicable.
_Avoid_: Region, location, when the point is regulatory/guidance applicability rather than geography generally.

**Corpus Document**:
A single ingested source document (for example, a guide, regulatory opinion, or survey report) carrying provenance, licence, jurisdiction, and freshness metadata.
_Avoid_: Source when referring only to the underlying passages rather than the whole document record.

**Passage**:
A retrievable chunk of text within a Corpus Document, small enough to be individually cited.
_Avoid_: Chunk when precision about its role as the citable unit matters; avoid Corpus Document when a specific citable span, not the whole document, is meant.

**Query**:
A Beekeeper's natural-language question submitted to the system.
_Avoid_: Question when the point is the persisted, workspace-owned record rather than the general concept.

**Answer**:
The system's response to a Query, grounded in cited Passages, or explicitly marked as having no grounded response.
_Avoid_: Response when the distinction between grounded and ungrounded output matters.

**Citation**:
The recorded link between an Answer and the specific Passage(s) it is grounded in.
_Avoid_: Source when referring to the link itself rather than the Corpus Document or Passage.

**Grounding Status**:
Whether an Answer is grounded in cited Passages, partially grounded in adjacent but incomplete Passages, or has no grounded Passages at all.
_Avoid_: Confidence when the point is citation coverage rather than the system's certainty in a claim.

**Source Supersession**:
A recorded relationship where one Corpus Document has been superseded by a successor document, such as a discontinued survey replaced by a new one.
_Avoid_: Deprecated when the point is that a specific successor document exists and should be preferred.

**Source Conflict**:
A recorded instance where two or more Corpus Documents materially disagree on guidance relevant to the same Query.
_Avoid_: Error when the disagreement is between legitimate authoritative sources rather than a system mistake.

**Answer Generation Version**:
A named version of the retrieval and generation configuration (embedding model, generation model, prompt template, and corpus snapshot) that produced a given Answer.
_Avoid_: Model Version without qualification — this parallels HiveSight's Model Version concept but versions a retrieval-and-generation pipeline, not a trained detector.

**Proposed Treatment**:
The Advisor's own record that it suggested a treatment for a hive (identified by HiveSight's own, opaque hive ID) in response to an inbound request from HiveSight. Its status is one of suggested (awaiting a response), completed (confirmed applied), or rejected (superseded by a revised Proposed Treatment produced after HiveSight rejected it with a reason — see Slice 0009's reject-and-revise loop).
_Avoid_: Treatment history when the point is what HiveSight itself records as actually applied — HiveSight, not the Advisor, is the system of record for that; a Proposed Treatment is only the Advisor's own recommendation trail.

## Terms Deliberately Not Imported (Yet)

**Review Decision**: HiveSight uses this for human review of annotations, corrections, and model releases. This product's domain model reserves an equivalent concept for Corrections, but it is dormant in version one — every Correction is trusted directly (confirmed via grilling; see `requirements/decision-log.md`, Correction Trust Level For V1). Do not build review-gate UI or enforcement against it yet; the concept exists so it is cheap to activate later, not because it is active now.

**Dataset Version / Training Run / Model Candidate / Benchmark Evaluation**: HiveSight's model-training lifecycle concepts do not apply to this product's Phase 1 — there is no trained model in this codebase, only a retrieval-and-generation pipeline over a curated corpus. If a Phase 1.x or later effort introduces a benchmark question/answer evaluation set (see `requirements.md` FR-007's correction-as-evaluation-evidence intent), that will warrant its own lightweight equivalent at that time, not a premature import of HiveSight's heavier model-governance vocabulary.
