# Vertical Slice 0008: Agentic Treatment Plan Request

## Purpose

HiveSight requests a treatment plan for a specific hive on a Beekeeper's behalf. The Advisor answers with a grounded recommendation (reusing the existing retrieval-and-generation pipeline) and durably records that it made the suggestion, so that when HiveSight later confirms the treatment was actually completed, the Advisor's own recommendation trail can be closed off — even if that confirmation arrives days or weeks later. This is the first slice of FR-009 (Phase 2, The Advisor) and the first genuinely agentic behaviour in this codebase: a workflow that must suspend and later resume, not just execute start-to-finish in one request.

It is also the first cross-application integration point between HiveSight and HiveSight Advisor, which have otherwise been kept architecturally independent (see `requirements/decision-log.md`, V1 Scope Boundary and the system-context "architecturally independent" framing).

## Source Inputs

- `requirements/requirements.md` FR-009, FR-010, FR-011.
- `requirements/roadmap.md` — FR-009/010/011 entries, scoped through discussion on 2026-08-04 (trigger shape, system-of-record split, LangGraph suggest→wait→resume shape, HiveSight-side prerequisite, shared-hive-identity question).
- `requirements/decision-log.md` — V1 Scope Boundary (Phase 2 gated on Phase 1 trust), Correction Trust Level For V1 and Corpus Curator CLI Tooling decisions (precedent for "advisory/thin tool, not a heavy gate" and "stub now, swap adapter later" patterns reused here).
- `architecture/system-context.md` — architectural independence from HiveSight; embedding/generation provider trust boundary reused for this slice's own external calls.
- `CONTEXT.md` — existing vocabulary (`Beekeeper`, `Jurisdiction`, `Answer`, `Citation`) reused; this slice adds `Proposed Treatment` (see Data Shape).

## User Path

```gherkin
Feature: Agentic Treatment Plan Request

  Scenario: HiveSight requests a treatment plan and the recommendation is grounded
    Given a hive in the UK jurisdiction with a recent high mite count
    And a valid HiveSight service credential
    When HiveSight requests a treatment plan for that hive
    Then the Advisor returns a grounded treatment recommendation with citations
    And the Advisor records a Proposed Treatment awaiting completion for that hive

  Scenario: A request without a valid service credential is rejected
    Given a request for a treatment plan without a valid HiveSight service credential
    When the request is submitted
    Then the Advisor rejects the request as unauthorized
    And no Proposed Treatment is recorded

  Scenario: No relevant guidance exists for the requested hive's situation
    Given a hive whose situation has no closely matching guidance in the corpus
    When HiveSight requests a treatment plan for that hive
    Then the Advisor honestly reports it has no grounded recommendation
    And no Proposed Treatment is recorded

  Scenario: HiveSight confirms a suggested treatment was completed
    Given a Proposed Treatment previously suggested for a hive
    When HiveSight confirms that treatment was completed
    Then the Proposed Treatment's status becomes completed
    And the Advisor's own recommendation trail for that hive is marked fulfilled
```

Signed off verbatim during scoping (2026-08-05); do not reword without re-confirming.

## Preconditions

- The caller (HiveSight, or a test standing in for it) presents a valid HiveSight service credential — a shared-secret header, checked against a configured value. This is a distinct auth seam from the existing Beekeeper `X-Dev-User-Id` dev-header; holding a valid service credential grants access only to the routes in this slice's dedicated router, never to Beekeeper-facing or Corpus Curator routes.
- The hive referenced in the request is identified by HiveSight's own hive ID, treated as an opaque foreign identifier — the Advisor does not model Hive as its own domain entity (closes the shared-hive-identity question from `roadmap.md`).
- No Workspace/Beekeeper login context is required for this call — it is app-to-app, not a Beekeeper session.

## End-To-End Behaviour

There is no Advisor-side UI in this slice — HiveSight is the only UI surface FR-009 was ever meant to have (per the 2026-08-04 roadmap discussion). The thin path is API-to-API:

1. HiveSight (or, in this slice, a test/script standing in for it) calls the Advisor's inbound endpoint with a hive ID, jurisdiction, and enough situational context to form a Query (e.g. the mite count that prompted the request).
2. The Advisor authenticates the caller via the service-credential dependency.
3. A LangGraph graph runs:
   - **Recommend** — reuses the existing `AnswerQueryWorkflow` (retrieval + generation) to produce a grounded Answer, exactly as the web UI's Query flow does today.
   - **Suggest** — if grounded, calls a stub `TreatmentSuggestionProvider` adapter (standing in for HiveSight's not-yet-built accept-suggestion endpoint) and persists a `Proposed Treatment` record with status `suggested`.
   - **Wait** — the graph suspends via a Postgres-backed LangGraph checkpointer. This is a real suspend, not a synchronous block — the process can restart and the suspended graph must still be resumable.
4. The Advisor's synchronous response to the inbound call carries the grounded recommendation (or the honest "no grounded recommendation" result) — HiveSight does not have to wait on the suspended graph to get an answer.
5. Later, a second, explicit test-only endpoint simulates HiveSight's future "treatment completed" webhook, resuming the suspended graph:
   - **Resume/close** — the `Proposed Treatment` status becomes `completed`, and the Advisor's own recommendation trail is marked fulfilled.

## Layers Touched

- Web UI: Not touched.
- Advisor API: New `/integrations/hivesight/*` router — `POST` to request a treatment plan, `POST` to confirm completion (test-only stand-in for HiveSight's future webhook). New `HiveSightServiceAuthDep` dependency, separate from `DevUserIdDep`.
- Service Workflow: New LangGraph graph (`Recommend` → `Suggest` → `Wait` → `Resume`) wrapping the existing `AnswerQueryWorkflow`. New `TreatmentSuggestionProvider` protocol + stub adapter (same Protocol/stub/live pattern as `EmbeddingProvider`/`GenerationProvider`).
- Storage: New `proposed_treatments` table (Postgres, same database) — one row per suggestion, holding the foreign hive ID, jurisdiction, the Answer/citations it suggested, and status. LangGraph's own checkpoint state also persists to Postgres (new checkpointer tables, managed by LangGraph itself).
- Contracts: New request/response shapes for the two `/integrations/hivesight/*` endpoints — this is the actual contract HiveSight's future implementation must match.
- Observability: Not touched beyond whatever default FastAPI/uvicorn logging already exists — no new structured logging in this slice.

## Test Seams

- Seam: `HiveSightServiceAuthDep` (new FastAPI dependency).
  Behaviour verified: valid credential passes, missing/invalid credential is rejected with 401, and rejection never reaches the graph or persists a `Proposed Treatment`.
  Test style: unit/integration (FastAPI `TestClient`).

- Seam: `TreatmentSuggestionProvider` protocol + stub adapter.
  Behaviour verified: called exactly when a grounded recommendation exists; never called when the recommendation is ungrounded.
  Test style: unit, with a fake/spy implementation of the protocol (same pattern as `_FakeGenerationProvider` in `test_answer_query_workflow.py`).

- Seam: the LangGraph graph itself (`Recommend`/`Suggest`/`Wait`/`Resume`).
  Behaviour verified: a grounded request produces a `suggested` `Proposed Treatment` and suspends; an ungrounded request produces no `Proposed Treatment` and does not suspend; a completion confirmation resumes a suspended graph and transitions status to `completed`.
  Test style: integration, against a real Postgres-backed checkpointer (in the test database) — an in-memory checkpointer would not prove the suspend is genuinely durable, which is the entire point of this slice.

- Seam: `POST /integrations/hivesight/treatment-plans` and the completion-confirmation endpoint.
  Behaviour verified: all four Gherkin scenarios above, end to end via `TestClient` — no Playwright, since there is no UI in this slice.
  Test style: API-level Gherkin (pytest-bdd or equivalent step definitions calling `TestClient` directly), consistent with the roadmap's existing "move Gherkin toward the API where there's no UI seam to prove" direction.

## Data Shape

- `proposed_treatments` table: `id`, `hive_id` (opaque, HiveSight-owned identifier), `jurisdiction_code`, `answer_id` (FK to the existing `answers` table — reuses the grounded Answer/Citation this recommendation is based on), `status` (`suggested` | `completed`), `created_at`, `completed_at`.
- New domain term for `CONTEXT.md`: **Proposed Treatment** — the Advisor's own record that it suggested a treatment for a (HiveSight-owned) hive, and whether that suggestion has been confirmed completed. Distinct from HiveSight's own treatment-history record, which stays entirely outside this codebase per the system-of-record split already agreed in `roadmap.md`.
- Request contract for `POST /integrations/hivesight/treatment-plans`: `hive_id` (string), `jurisdiction_id` (UUID — matches the existing `jurisdiction_id` used throughout the rest of this codebase, not a new `code`-based lookup), `situational_context` (free text, becomes the underlying Query text).
- Request contract for `POST /integrations/hivesight/treatment-plans/completions`: `hive_id` (implemented as hive ID rather than Proposed Treatment ID — HiveSight naturally knows the hive, not the Advisor's internal record ID).

## Out Of Scope

- HiveSight's own two endpoints (accept-suggestion, completion webhook) — those are HiveSight's build, tracked on its own roadmap. This slice only builds the Advisor's side, against stubs/test-only stand-ins.
- Any real service-to-service credential infrastructure beyond a static shared secret (OAuth2 client-credentials, mTLS) — named as the deliberate future upgrade path if this ever needs more than one external caller.
- Modelling "Hive" as a first-class Advisor domain entity — it stays an opaque foreign ID.
- Any UI change in the Advisor's own web app — HiveSight is the only UI surface for this flow.
- A "did it work?" follow-up comparing pre/post-treatment inspection history — flagged in `roadmap.md` as a future extension once this loop exists, not built now.
- Real user authentication for Beekeeper-facing routes — unrelated to this slice's service-to-service auth seam; remains a separate, already-tracked roadmap item.

## Acceptance Criteria

- [x] All four signed-off Gherkin scenarios pass via API-level tests (`TestClient`), no browser involved. See `tests/test_hivesight_integration_router.py`.
- [x] The completion-confirmation test demonstrates the graph resuming from a genuinely persisted (Postgres-backed) checkpoint, not an in-memory one. `test_treatment_plan_workflow.py::test_confirm_completed_resumes_and_marks_the_treatment_completed` resumes via a freshly opened `PostgresSaver` connection and a newly compiled graph object — not the same in-process object that created the suspend — to prove the state survived in Postgres itself.
- [x] `HiveSightServiceAuthDep` is wired only to the new `/integrations/hivesight/*` router, never to existing Beekeeper or Corpus Curator routes.
- [x] `TreatmentSuggestionProvider` follows the existing Protocol/stub/live adapter pattern, with only a stub implementation in this slice.
- [x] `CONTEXT.md` gains the `Proposed Treatment` term.
- [x] `requirements/decision-log.md` gains an entry covering: the LangGraph graph shape and persistence requirement, the shared-hive-identity resolution (HiveSight's ID is canonical, opaque to the Advisor), and the service-to-service auth pattern (shared-secret header, scoped by router, OAuth2 as future upgrade).
- [x] `requirements/traceability.md` is updated to map FR-009 to these scenarios.

## Implementation Notes

- Reusing `AnswerQueryWorkflow` for the `Recommend` node surfaced a real gap not caught during scoping: every `Query`/`Answer` row is `Workspace`-scoped (`NOT NULL` FK), but this inbound call has no Beekeeper/Workspace context. Resolved by grilling a follow-up question with the user: a dedicated internal "system" `Workspace` row, seeded via `migrations/0006_slice_0008_system_workspace.sql` (`SYSTEM_WORKSPACE_ID`), used only for agentic requests — not a real Beekeeper's Workspace, and no schema loosening of the existing `NOT NULL` constraint.
- `langgraph`/`langgraph-checkpoint-postgres` checkpoint tables are set up via a new `setup_checkpointer()` step in `db.py`, wired into the existing `migrate`/`migrate-test`/`reset-test` CLI commands — kept as an explicit step alongside `apply_migrations`, not automatic at app startup, matching this project's existing "migrations run explicitly" convention.
- `POST /integrations/hivesight/treatment-plans/completions` takes `hive_id`, not the `Proposed Treatment` ID as the slice doc originally sketched — HiveSight naturally knows the hive it's confirming, not the Advisor's internal record ID.

## Open Questions

None outstanding — all design questions from scoping were resolved and signed off (2026-08-05).
