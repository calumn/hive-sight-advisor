# Requirements

**Status: grilled and confirmed for v1 scope. See `decision-log.md` for the reasoning behind each confirmed item. Numbering is stable for traceability.**

## Foundational

- **FR-000**: The system shall model `Workspace`, `Workspace Membership`, and roles in the same shape as HiveSight's `CONTEXT.md`, even though v1 supports a single user in practice via deferred/dev-level authentication, matching HiveSight's own current depth. This is a domain-modelling decision, not an authentication commitment — confirmed via grilling, see `decision-log.md`.

## Phase 1: Grounded Knowledge

- **FR-001**: The system shall answer a beekeeper's natural-language question about Varroa monitoring and management using retrieval grounded in a curated corpus, not unaided generation.
- **FR-002**: Every answer shall cite the specific source passage(s) it is grounded in.
- **FR-003**: The system shall determine or ask which jurisdiction a question applies to, and shall not blend guidance from different jurisdictions into a single unattributed answer. V1 corpus covers US and UK only (confirmed via grilling, see `decision-log.md`); EU coverage is deferred and must be modelled at member-state granularity when added, not as a single "EU" jurisdiction.
- **FR-004**: Given a described situation (mite count, season, brood presence, region), the system shall compare applicable treatment options against the corpus, surfacing trade-offs (temperature constraints, organic-certification compatibility, withdrawal periods) rather than a single unexplained recommendation.
- **FR-005**: The system shall flag when a source it would otherwise cite has been superseded by a newer or successor source, rather than citing it as current.
- **FR-006**: The system shall surface it explicitly, rather than silently resolving it, when two authoritative sources in the corpus materially disagree.
- **FR-007**: The system shall provide a way for the user to flag an answer as wrong or misleading, and shall retain that correction as evaluation evidence. Correction is modelled as workspace-scoped, consistent with FR-000's `Workspace`/`Membership` modelling, but for v1 every correction is treated as trusted evidence directly, with no separate review gate — confirmed via grilling, see `decision-log.md`.
- **FR-008**: When a question has no relevant grounding in the corpus, the system shall not answer from unsourced general knowledge. It shall say explicitly that it has no grounded answer, and shall offer the closest related grounded material if any exists, clearly labelled as a partial match rather than a direct answer.

## Phase 2: The Advisor

**Out of scope for v1** (confirmed via grilling, see `decision-log.md`). Captured here so the shape is not lost, not because it is being built now.

- **FR-009**: Given hive/apiary context and history, the system shall draft a proposed treatment schedule and present it for explicit human approval before it is treated as an accepted plan.
- **FR-010**: The system shall support recording what was applied, when, and at what dose, against a hive's treatment history.
- **FR-011**: The system may incorporate HiveSight photo-based mite-count data, where available, as an optional data source to inform Phase 2 proposals. Confirmed: this is a data-source relationship only, not an identity or access dependency — the Advisor is not gated behind a HiveSight `Workspace`, now or by default later. A tighter commercial/packaging tie-in between the two products is possible but is an explicit future business decision, not an architectural assumption of v1.

## Non-Functional

- **NFR-001**: The system shall not present its output as an official diagnosis, treatment prescription, or regulatory determination. Phase 1 output is decision support; Phase 2 output is a proposal awaiting human approval.
- **NFR-002**: Phase 1 (grounded-knowledge) output and Phase 2 (proposed-action) output shall be visibly and unambiguously distinguished from each other wherever both exist in the product.
- **NFR-003**: Source documents shall carry provenance and licence metadata (at minimum: source, licence terms, retrieval/version date), given that corpus sources carry different reuse terms (for example, the HBHC guide's CC BY-NC-ND terms and Apidologie's 12-month open-access embargo).
- **NFR-004**: The system shall not require HiveSight to be installed or in use in order to provide Phase 1 or Phase 2 functionality.

## Open Questions Carried Into Grilling

All resolved as of 2026-07-31 — see `decision-log.md` for the full reasoning behind each:

- ~~Is Phase 1 alone the intended v1 scope...~~ — V1 Scope Boundary.
- ~~Is the primary persona...~~ — Primary Persona And Multi-User Modelling.
- ~~Advisor/HiveSight coupling...~~ — Advisor Independence From HiveSight.
- ~~How many jurisdictions...~~ — V1 Jurisdiction Scope.
- ~~No-grounding behaviour...~~ — No-Grounding Behaviour; captured as FR-008.
- ~~Correction/feedback trust level...~~ — Correction Trust Level For V1; captured in FR-007.
