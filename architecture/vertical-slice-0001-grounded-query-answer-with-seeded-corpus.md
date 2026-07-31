# Vertical Slice 0001: Grounded Query Answer With Seeded Corpus

## Purpose

Prove the core value loop: a Beekeeper asks a natural-language Varroa question and gets back an Answer grounded in a real corpus Passage, with a Citation — not unaided generation. This is the smallest slice that demonstrates the product's actual value proposition (FR-001, FR-002) rather than the ingestion machinery around it.

## Source Inputs

- FR-000 (`Workspace`/`Membership` modelling, dev-auth deferred)
- FR-001 (grounded retrieval answering)
- FR-002 (mandatory citation)
- FR-003 / V1 Jurisdiction Scope decision — scoped down to a single jurisdiction for this slice; see Out Of Scope
- Decision log: V1 Application Surface, Service Topology, Generation And Embedding Providers, Database Technology, Jurisdiction Resolution
- `architecture/domain-model.md`: `Workspace`, `User`, `Workspace Membership`, `Query`, `Answer`, `Citation`, `Passage`, `Corpus Document`, `Jurisdiction`

## User Path

Given a dev-authenticated Beekeeper `User` with a `Workspace Membership`, and one `Corpus Document` with at least one `Passage` hand-seeded directly into the Corpus Store for the UK `Jurisdiction`
When the Beekeeper submits a natural-language `Query` with Jurisdiction = UK through the web app
Then the Advisor Service embeds the Query, retrieves the seeded Passage via pgvector similarity search, calls Claude to generate an `Answer` grounded in that Passage, and the web app displays the Answer with a `Citation` linking back to the Passage and its source Corpus Document

## Preconditions

- Dev-authenticated User context and Workspace Membership, matching HiveSight's dev-auth header pattern — no real authentication.
- Exactly one Corpus Document, with its Passage(s) and embeddings, hand-inserted directly into the Corpus Store via a seed script — not through a built ingestion pipeline. This is the explicit, isolated stub for this slice.
- No consent/policy gate beyond Workspace Membership; no Data Use Agreement equivalent exists yet in this product.

## End-To-End Behaviour

Beekeeper opens the web app, is resolved as the dev-authenticated User, selects Jurisdiction = UK, types a Query, submits. The Advisor Service embeds the Query text via Voyage AI, runs a pgvector similarity search against the seeded Passage embeddings scoped to Jurisdiction = UK, calls Claude with the retrieved Passage(s) as grounding context and an instruction to answer only from that context, persists Query/Answer/Citation, and returns the result. The web app renders the Answer text with a visible Citation (source document name plus passage excerpt).

## Layers Touched

- Web UI: Query input with Jurisdiction selector, Answer display with Citation.
- Core API (Advisor Service): Query submission endpoint, Answer retrieval endpoint.
- Analysis Service: Not touched — no such service exists in this architecture (Service Topology decision).
- Storage: Postgres — `Workspace`, `User`, `Workspace Membership`, `Jurisdiction`, `Corpus Document`, `Passage` (hand-seeded), `Query`, `Answer`, `Citation`.
- Queue or async boundary: Not touched — synchronous request/response only, no async job exists in this architecture.
- Contracts: Query request/response shape between web app and Advisor Service.
- Observability: Not touched — deferred until a real cross-service or diagnostic need exists.

## Test Seams

- Seam: retrieval function (embed Query, pgvector similarity search). Behaviour verified: given a seeded Passage and a semantically related Query, the correct Passage is retrieved. Test style: integration test against a real Postgres/pgvector test database with a seeded fixture.
- Seam: generation call boundary. Behaviour verified: given retrieved Passage(s), the generated Answer is non-empty and its Citation references the correct Passage id. Test style: integration test against a stubbed Claude fixture in the default suite; a real Claude call is exercised manually or via a separate live test not run on every commit, to avoid unnecessary API spend on every run.
- Seam: Query submission API endpoint. Behaviour verified: a dev-authenticated request with valid Workspace Membership returns an Answer with a Citation; a request without valid membership is rejected. Test style: integration tests with dependency overrides and dev-auth headers, matching HiveSight's existing test style convention.

## Data Shape

- Corpus Document: id, jurisdiction_id, title, source, licence_terms, status (`current`)
- Passage: id, corpus_document_id, text_content, embedding
- Query: id, workspace_id, text, resolved_jurisdiction_id
- Answer: id, query_id, text, grounding_status (`grounded`)
- Citation: id, answer_id, passage_id

## Out Of Scope

- Corpus Ingestion pipeline (fetch, chunk, embed) — the Passage is hand-seeded via a script, not ingested through a built pipeline. Deferred to a follow-on slice.
- Multi-jurisdiction blending prevention (FR-003 in full) — only one jurisdiction is seeded here, so there is nothing to blend yet. A second slice with two jurisdictions is needed to actually prove FR-003.
- No-grounding behaviour (FR-008) — this slice only exercises the grounded/success path.
- Source supersession, conflict detection, treatment comparison, corrections (FR-004 through FR-007).
- Real authentication — dev-auth only, matching HiveSight's current depth.
- Observability/structured logging.

## Acceptance Criteria

- [ ] A dev-authenticated Beekeeper can submit a Query with a Jurisdiction through the web app.
- [ ] The Advisor Service retrieves the seeded Passage via a real pgvector similarity search, not a hardcoded lookup.
- [ ] The returned Answer is generated by Claude using only the retrieved Passage as grounding context.
- [ ] The Answer is displayed with at least one Citation pointing to the correct Passage and Corpus Document.
- [ ] A request without a valid Workspace Membership is rejected.
- [ ] Integration tests cover the retrieval, generation-boundary, and API seams above.
- [ ] The generation-boundary test runs against a stubbed Claude fixture in the default suite, not a real API call, to avoid unnecessary spend on every test run.
- [ ] The hand-seeded Passage is created via a checked-in, rerunnable seed script, not a one-off manual insert.

## Open Questions

Both resolved via grilling — see `requirements/decision-log.md`, Slice 0001 Test And Seed Approach.

- ~~Should the Claude generation call be exercised for real in automated tests, or stubbed?~~ — resolved: stubbed behind a documented fixture in the default automated suite; a real call is exercised manually, or via a separate live test not run on every commit, before the slice is considered done.
- ~~Is a checked-in, rerunnable seed script the right form for the hand-seeded Passage, or a one-off manual insert?~~ — resolved: a checked-in seed script, reusable for slice 2's second jurisdiction.
