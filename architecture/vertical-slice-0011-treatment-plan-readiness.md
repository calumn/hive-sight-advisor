# Vertical Slice 0011: Treatment Plan Readiness

## Purpose

Closes four Advisor-side contract gaps surfaced by reviewing HiveSight's Slice 0029 and Slice 0029.5 designs: a brittle internal-UUID jurisdiction field, no response contract versioning, no audit-correlation id, and a real bug (verified empirically) where a repeated treatment-plan request for the same hive silently orphans an unresolved suggestion. None of these are hypothetical — all four were found while reviewing what HiveSight is actually about to build against this contract, and fixing them now (before any real caller exists) is far cheaper than after.

## Source Inputs

- `requirements/hivesight-slice-0029-review-response.md` and `requirements/hivesight-slice-0029-5-review-response.md` — the two review responses that surfaced these four gaps, including the empirical proof of the orphaned-suggestion bug.
- `requirements/decision-log.md`, "Agentic Treatment Plan Request Mechanism" and "Reject-And-Revise Treatment Plan Mechanism" — the existing contract and graph shape this slice modifies, not replaces.
- Grilling session (2026-08-06), four questions, this slice.
- `hivesight-advisor-integration-contract` skill — updated as part of this slice's closeout, since these are real, implemented contract changes.

## User Path

```gherkin
Feature: Treatment Plan Readiness

  Scenario: A treatment plan request succeeds with a jurisdiction code and carries audit fields
    Given a hive in the UK jurisdiction with a recent high mite count
    When HiveSight requests a treatment plan for that hive using jurisdiction code "uk"
    Then the Advisor returns a grounded treatment recommendation
    And the response includes the contract version
    And the response includes the answer id

  Scenario: A request with an unknown jurisdiction code is rejected
    When HiveSight requests a treatment plan using jurisdiction code "de"
    Then the Advisor rejects the request as an unknown jurisdiction
    And no Proposed Treatment is recorded

  Scenario: Repeating a request while a suggestion is still pending returns the same suggestion
    Given a Proposed Treatment already suggested for a hive, awaiting a decision
    When HiveSight requests a treatment plan again for that same hive
    Then the Advisor returns the existing pending suggestion
    And no second Proposed Treatment is recorded

  Scenario: Requesting again after a suggestion was completed starts a fresh episode
    Given a hive whose previous Proposed Treatment was confirmed completed
    When HiveSight requests a new treatment plan for that hive
    Then the Advisor drafts a genuinely new recommendation
    And a new Proposed Treatment is recorded

  Scenario: Confirming a suggestion includes the answer id for audit correlation
    Given a Proposed Treatment previously suggested for a hive
    When HiveSight confirms that treatment was completed
    Then the response includes the answer id the confirmed suggestion was based on

  Scenario: Rejecting a suggestion includes the contract version and answer id
    Given a Proposed Treatment previously suggested for a hive
    When HiveSight rejects it with a reason
    Then the revised recommendation response includes the contract version
    And the revised recommendation response includes the answer id
```

Signed off verbatim during scoping (2026-08-06); do not reword without re-confirming.

## Preconditions

- Same service-credential auth as Slices 0008/0009 — unchanged.
- A `jurisdictions` table with `code`/`id` already exists (Slice 0001) — no migration needed for the jurisdiction-code lookup itself.

## End-To-End Behaviour

**Jurisdiction code, not UUID** (Question 1): `TreatmentPlanRequest` drops `jurisdiction_id: UUID` and gains `jurisdiction_code: str`. A new `JurisdictionRepository.find_id_by_code(code)` resolves it to Advisor's internal UUID at the router boundary, before anything touches `AnswerQueryWorkflow` or `TreatmentPlanWorkflow` — neither of those, nor `CorpusRepository`, nor `TreatmentPlanState`, change at all; they keep using the internal UUID exactly as today. An unknown code returns `422` with no `Proposed Treatment` recorded.

**Contract version** (Question 2): a single shared constant (`CONTRACT_VERSION = "treatment_plan_v1"`) is added to all three response bodies on the `/integrations/hivesight/*` router — request, completion, and rejection.

**Answer id** (Question 3): `Answer.id` is exposed as `answer_id` in `TreatmentPlanResponse` and `TreatmentRejectionResponse` (both already carry a fresh `Answer`); `ProposedTreatmentResponse` (the completion response) also gains `answer_id`, sourced from the `ProposedTreatment.answer_id` it already stores internally.

**Idempotent requests** (Question 4): `TreatmentPlanWorkflow.request_treatment_plan` peeks at existing graph state via `get_state` before invoking anything, exactly the pattern `reject_treatment` already uses. If a `proposed_treatment_id` is already present in state, its **current** status is looked up via `ProposedTreatmentRepository.find_by_id` (not inferred from graph-state fields, which can't reliably distinguish "still pending" from "fully completed" on their own):
  - `suggested` → return the existing answer from state; no graph invocation, no new row.
  - `completed` (or `rejected` — which can be the state's dangling reference after an ungrounded revision, see Implementation Notes) → proceed with a genuinely fresh `graph.invoke`, exactly as today.

## Layers Touched

- Web UI: Not touched.
- Advisor API: `routers/hivesight_integration.py` — request/response model changes on all three endpoints; new jurisdiction-code resolution and its 422 error path.
- Service Workflow: `TreatmentPlanWorkflow.request_treatment_plan` gains the peek-and-possibly-short-circuit logic. `_recommend`, `_suggest`, `_wait_and_resume`, and the graph topology are unchanged — this is purely additional logic in one existing method.
- Storage: No migration. New `JurisdictionRepository` (read-only) against the existing `jurisdictions` table.
- Contracts: Breaking change to the treatment-plans request (`jurisdiction_id` → `jurisdiction_code`) and additive changes to all three responses (`contract_version`, `answer_id`). See "Contract Changes For HiveSight" below for the exact shapes to hand off.
- Observability: Not touched.

## Test Seams

- Seam: `JurisdictionRepository.find_id_by_code`.
  Behaviour verified: a known code resolves to the correct UUID; an unknown code returns `None`.
  Test style: unit/integration against Postgres.

- Seam: `TreatmentPlanWorkflow.request_treatment_plan`'s idempotency check.
  Behaviour verified: a second call while the first is still `suggested` returns the same `Answer` (same `id`) and creates no second `proposed_treatments` row; a second call after the first was `completed` proceeds normally and creates a genuinely new row.
  Test style: integration, against the real Postgres-backed checkpointer — same durability bar as Slices 0008/0009, since this touches the same suspend/resume state.

- Seam: `/integrations/hivesight/treatment-plans`, `/treatment-plans/completions`, `/treatment-plans/rejections`.
  Behaviour verified: all six signed-off scenarios, end to end via `TestClient`, including the 422 unknown-jurisdiction path and both audit fields (`contract_version`, `answer_id`) on every response.
  Test style: API-level, plain descriptively-named pytest functions with scenario text in the docstring — same convention as Slices 0008/0009.

## Data Shape

No schema migration. New read-only repository against the existing `jurisdictions` table.

## Contract Changes For HiveSight

**Request — `POST /integrations/hivesight/treatment-plans`** (breaking change):

```json
{
  "hive_id": "string",
  "jurisdiction_code": "uk",
  "situational_context": "string"
}
```

`jurisdiction_id` (UUID) is removed. `jurisdiction_code` is a stable, short lowercase code (`"uk"`, `"us"` today) — this is the identifier meant to be stable across the service boundary, unlike an internal primary key.

**Response — `POST /integrations/hivesight/treatment-plans`** and **`POST /integrations/hivesight/treatment-plans/rejections`** (additive):

```json
{
  "contract_version": "treatment_plan_v1",
  "answer_id": "uuid",
  "text": "string",
  "grounding_status": "grounded | partial | ungrounded",
  "citations": [ { "...": "unchanged" } ]
}
```

The rejections response additionally keeps its existing `revision_exhausted: boolean` field, unchanged.

**Response — `POST /integrations/hivesight/treatment-plans/completions`** (additive):

```json
{
  "contract_version": "treatment_plan_v1",
  "id": "uuid",
  "answer_id": "uuid",
  "status": "completed"
}
```

**New behaviour, no shape change**: calling the treatment-plans endpoint again for a hive that already has a pending (`suggested`) recommendation now returns that same recommendation (same `answer_id`) instead of generating a new, competing one — closing the orphaned-suggestion bug found during review. Calling it again after a prior recommendation was completed correctly starts a new one.

## Out Of Scope

- Any change to `AnswerQueryWorkflow`, `CorpusRepository`, or `TreatmentPlanState` — the jurisdiction-code fix is entirely a boundary translation, not a change to Advisor's internal representation.
- A distinguishing flag (e.g. `is_new`) on the idempotent-short-circuit response — deliberately not added; the response is indistinguishable from a fresh one by design (Question 4).
- Backward-compatible support for the old `jurisdiction_id` UUID field — this is a clean breaking change, made now because no real caller exists yet.
- Updating the shared `hivesight-advisor-integration-contract` skill until this slice is implemented and verified (matches the skill's own stated update policy, and HiveSight's own stated policy for its Slice 0029/0029.5 work).

## Acceptance Criteria

- [x] All six signed-off Gherkin scenarios pass via API-level tests (`TestClient`). See `tests/test_treatment_plan_readiness_router.py`.
- [x] `jurisdiction_id` is fully removed from the request contract; only `jurisdiction_code` is accepted.
- [x] An unknown jurisdiction code returns 422 with no `Proposed Treatment` recorded.
- [x] `contract_version` and `answer_id` appear on all three response shapes.
- [x] A repeated request while a suggestion is `suggested` returns the identical `Answer` and creates no second `proposed_treatments` row — verified against the real Postgres-backed checkpointer.
- [x] A repeated request after the prior suggestion was `completed` creates a genuinely new `proposed_treatments` row.
- [x] No behavioural change to the reject-and-revise loop itself (Slice 0009's own tests pass unmodified — updated only to use `jurisdiction_code` in their request payloads).
- [x] `requirements/decision-log.md` gains an entry covering all four grilled decisions.
- [x] `requirements/hivesight-slice-0029-review-response.md` and `-0029-5-review-response.md`'s flagged items are marked resolved, pointing at this slice.
- [x] The shared `hivesight-advisor-integration-contract` skill is updated with the new contract shapes.

## Open Questions

None outstanding — all design questions from scoping were resolved and signed off (2026-08-06).
