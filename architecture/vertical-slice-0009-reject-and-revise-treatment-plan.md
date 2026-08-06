# Vertical Slice 0009: Reject-And-Revise Treatment Plan

## Purpose

Slice 0008 built a LangGraph workflow that could suspend and resume on acceptance, but had no genuine cycle — it was a straight line (`Recommend` → `Suggest` → `Wait`) plus one interrupt. This slice adds a real loop: when a suggested treatment is rejected with a reason, the graph returns to `Recommend` carrying that reason as new context, produces a revised suggestion, and repeats up to a cap before giving up. This is both a real product behaviour (a beekeeper's context — e.g. an active honey flow — can rule out an otherwise-reasonable suggestion) and the first genuinely cyclical graph in this codebase.

## Source Inputs

- `architecture/vertical-slice-0008-agentic-treatment-plan-request.md` — the graph, endpoints, and `Proposed Treatment` concept this slice extends.
- `requirements/decision-log.md`, "Agentic Treatment Plan Request Mechanism" — the shared-secret auth pattern and stub-adapter approach this slice reuses unchanged.
- `requirements/decision-log.md`, "User Corrections Mechanism" and "Source Supersession Mechanism" — the append-only precedent (never mutate a past record in place; point to what it superseded) this slice's persistence model follows.
- Grilling sessions (2026-08-05): six questions during initial scoping, plus four follow-up questions during a pre-implementation "grill me" pass.

## User Path

```gherkin
Feature: Reject And Revise A Suggested Treatment

  Scenario: HiveSight rejects a suggested treatment and receives a revised recommendation
    Given a Proposed Treatment previously suggested for a hive
    When HiveSight rejects it with a reason
    Then the Advisor drafts a revised grounded treatment recommendation that accounts for that reason
    And the previous Proposed Treatment is marked rejected
    And a new Proposed Treatment is recorded as awaiting completion, superseding the rejected one

  Scenario: Repeated rejection eventually exhausts the revision limit
    Given a Proposed Treatment that has already been rejected and revised the maximum number of times
    When HiveSight rejects the latest suggestion again
    Then the Advisor returns its last recommendation flagged as having exhausted revisions
    And no further Proposed Treatment is recorded

  Scenario: Rejecting when nothing is awaiting completion is rejected
    Given no Proposed Treatment is currently suggested for a hive
    When HiveSight attempts to reject a treatment for that hive
    Then the Advisor rejects the request as not found

  Scenario: A revised recommendation itself has no grounded answer
    Given a Proposed Treatment previously suggested for a hive
    When HiveSight rejects it with a reason, and no grounded alternative exists in the corpus
    Then the Advisor honestly reports it has no grounded recommendation
    And no new Proposed Treatment is recorded
    And revisions are not reported as exhausted
```

Signed off verbatim during scoping and the follow-up grilling pass (2026-08-05); do not reword without re-confirming.

## Preconditions

- Same service-credential auth as Slice 0008 — this is app-to-app, no Beekeeper/Workspace context.
- A `Proposed Treatment` with status `suggested` must already exist for the hive (created by Slice 0008's `request_treatment_plan` flow) for a rejection to apply to.

## End-To-End Behaviour

1. HiveSight (or a test standing in for it) calls a new, test-only endpoint — `POST /integrations/hivesight/treatment-plans/rejections`, body `{hive_id, reason}` — mirroring Slice 0008's completion-confirmation endpoint exactly, since HiveSight's real rejection webhook doesn't exist yet either.
2. The Advisor first **reads** the suspended graph's state (`get_state`, not a resume) to check the current revision count — this decides which of the following paths applies, and matters because a genuine resume is a one-shot consumption of the interrupt; peeking first is the only way to support outcome 4 below without silently ending the episode.
3. **Below the cap** (fewer than 3 revisions so far, i.e. this would be at most the 4th suggestion overall — 1 original + up to 3 revisions): the Advisor genuinely resumes the graph with `{action: "reject", reason}`. The graph re-enters `Recommend`, with the rejection reason appended to the original query text (e.g. *"...A previously suggested treatment was rejected because: {reason}. Suggest an alternative that avoids this."*) — `AnswerQueryWorkflow`'s own interface is untouched; the loop lives entirely in the graph.
   - If the revised recommendation is grounded: `Suggest` runs again (the stub `TreatmentSuggestionProvider` is called again — a new suggestion is new information HiveSight needs), a **new** `proposed_treatments` row is inserted (`suggested`, `supersedes_proposed_treatment_id` pointing at the rejected row, whose own status becomes `rejected`), and the graph suspends again at `Wait`.
   - If the revised recommendation is ungrounded: no `Suggest` step runs and no new `Proposed Treatment` is recorded (same honest-no-answer rule as everywhere else in this codebase) — the response reports the ungrounded answer with `revision_exhausted: false`, since revisions were not used up, there simply wasn't a good answer this time. The rejected row from step 1 stays `rejected`, and there is deliberately no `suggested` row for this hive until a fresh `request_treatment_plan` call starts a new episode — this dead end is accepted as correct behaviour, not patched around, matching FR-008's existing stance that an honest "I don't know" is a valid outcome, not a bug.
4. **At the cap already** (the 4th rejection, i.e. 3 revisions already made): the graph is **not** resumed. The Advisor reads the last answer and `proposed_treatment_id` straight from the peeked state and returns them with `revision_exhausted: true`. Because the graph was never resumed, its suspended state is untouched — the last `Proposed Treatment` remains `suggested` and can still be accepted via `confirm_completed` at any time; exhaustion only forecloses further *revision*, not acceptance of what's already on the table.
5. Rejecting a hive with nothing currently `suggested` (already completed, or never requested — note "already exhausted" is no longer a distinct case, since an exhausted suggestion is still `suggested` per point 4) returns 404, exactly like the existing completion-confirmation endpoint's behaviour.

## Layers Touched

- Web UI: Not touched.
- Advisor API: New `POST /integrations/hivesight/treatment-plans/rejections` endpoint on the existing `/integrations/hivesight/*` router, same `HiveSightServiceAuthDep`.
- Service Workflow: `TreatmentPlanWorkflow`'s `_wait_and_resume` node now branches on the resume payload's `action` (`accept` vs `reject`) — accept behaves exactly as Slice 0008 (mark completed, end); reject increments `revision_count`, marks the current `Proposed Treatment` rejected, and conditionally routes back to `recommend` (a real cycle, not a DAG) when `revision_count` is still below `MAX_REVISIONS = 3`. The rejection endpoint itself peeks graph state via `get_state` before deciding whether to call `Command(resume=...)` at all — see End-To-End Behaviour, point 4.
- Storage: `proposed_treatments` gains `status = 'rejected'` as a valid value and a new nullable `supersedes_proposed_treatment_id` self-referencing column.
- Contracts: New request/response shapes for the rejection endpoint, including the `revision_exhausted` flag.
- Observability: Not touched.

## Test Seams

- Seam: `ProposedTreatmentRepository` — new `mark_rejected(id)` and `save(..., supersedes_proposed_treatment_id=...)` behaviour.
  Behaviour verified: a rejected row's status becomes `rejected`; a new row correctly records what it supersedes.
  Test style: unit/integration against Postgres, same pattern as Slice 0008's repository tests.

- Seam: `TreatmentPlanWorkflow`'s graph — the new reject/loop-back path and the revision cap.
  Behaviour verified: one rejection produces a revised answer and a new suggested `Proposed Treatment` superseding the old one; the 4th rejection (3 revisions already made) does not resume the graph, returns `revision_exhausted: true`, and leaves the last `Proposed Treatment` still `suggested` (confirmable via `confirm_completed` afterwards — this is the durability-relevant assertion, proving the peek-not-resume mechanic actually preserved the suspend); the stub `TreatmentSuggestionProvider` is called once per successful revision, not once total; a revision that comes back ungrounded records no new `Proposed Treatment` and reports `revision_exhausted: false`.
  Test style: integration, against the real Postgres-backed checkpointer — same durability bar as Slice 0008, since this is still the same suspend/resume mechanism, now exercised in a loop.

- Seam: `POST /integrations/hivesight/treatment-plans/rejections`.
  Behaviour verified: all four signed-off Gherkin scenarios, end to end via `TestClient`.
  Test style: API-level, plain descriptively-named pytest functions with scenario text in the docstring — same convention as Slice 0008's `test_hivesight_integration_router.py`.

## Data Shape

- `proposed_treatments` gains: `supersedes_proposed_treatment_id uuid REFERENCES proposed_treatments(id)` (nullable — null for an original, non-revised suggestion), and `'rejected'` added as a valid `status` value alongside the existing `'suggested'`/`'completed'`.
- Request contract for `POST /integrations/hivesight/treatment-plans/rejections`: `hive_id` (string), `reason` (free text).
- Response contract: on success, the same shape as the original treatment-plan response (`text`, `grounding_status`, `citations`) plus `revision_exhausted` (bool — `true` only when the cap was already reached before this call; `false` in every other case, including an ungrounded revision); 404 if nothing is awaiting completion for that hive.

## Out Of Scope

- Any change to HiveSight's side — the rejection endpoint here is a test-only stand-in for HiveSight's not-yet-built real webhook, exactly like Slice 0008's completion endpoint.
- Any UI change — HiveSight remains the only UI surface for this flow.
- Structured rejection reasons (a taxonomy of reject codes) — free text only, matching the existing precedent from Corrections (FR-007), which also chose free text over a taxonomy for the same reason: nothing yet consumes or aggregates these reasons in a way that would justify the extra structure.
- Tuning `MAX_REVISIONS` based on real usage data — 3 is a starting judgment call, not a calibrated number.

## Acceptance Criteria

- [x] All four signed-off Gherkin scenarios pass via API-level tests (`TestClient`), no browser involved. See `tests/test_hivesight_rejection_router.py`.
- [x] A rejection below the cap produces a new `proposed_treatments` row (`suggested`) pointing at the rejected one (`rejected`) via `supersedes_proposed_treatment_id` — never an in-place mutation of the rejected row's own content.
- [x] The revision cap is enforced by a real loop in the graph (a genuine cycle, verified by testing repeated rejections), not by an artificial early exit.
- [x] Reaching the cap does not resume the graph — verified by confirming the last `Proposed Treatment` is still `confirm_completed`-able after an exhausted rejection response. See `test_reject_treatment_exhausts_after_max_revisions_and_preserves_the_last_suggestion`.
- [x] An ungrounded revision records no `Proposed Treatment` and reports `revision_exhausted: false`, distinct from both a successful revision and cap exhaustion.
- [x] `requirements/decision-log.md` gains an entry covering all ten grilled decisions (the original six, plus the four follow-up points: exhaustion leaves the last suggestion acceptable, the 1-original-plus-3-revisions cap semantics, peek-before-resume mechanics, and the ungrounded-revision outcome).
- [x] `requirements/traceability.md`'s FR-009 row is updated to include this slice's scenarios.
- [x] `CONTEXT.md`'s `Proposed Treatment` entry is updated to note that a suggestion can now be superseded by a revised one, not only completed.

## Implementation Notes

- `_wait_and_resume` now branches on the resume payload's `action` field (`{"action": "accept"}` vs `{"action": "reject", "reason": ...}`), routing conditionally back to `recommend` only on reject. `confirm_completed`'s existing resume call was updated from the old bare `Command(resume=True)` to the new `{"action": "accept"}` shape — a small, required change to Slice 0008's code, not a new design decision.
- The rejection reason is *not* accumulated across revisions — each `_recommend` call appends only the latest rejection reason to the original, fixed `query_text`, not a running history of every past reason. This wasn't separately grilled; it's the natural reading of the slice doc's own wording ("the rejection reason appended to the original query text," singular) and keeps the prompt from growing unboundedly across revisions.
- `supersedes_proposed_treatment_id` for a new suggestion is simply whatever `proposed_treatment_id` was already in graph state before `_suggest` overwrites it — no separate tracking field was needed, since state naturally still holds the just-rejected id at exactly the point `_suggest` runs.

## Open Questions

None outstanding — all design questions from scoping and the follow-up grilling pass were resolved and signed off (2026-08-05).
