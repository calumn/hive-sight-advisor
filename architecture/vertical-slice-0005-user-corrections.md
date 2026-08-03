# Vertical Slice 0005: User Corrections

## Purpose

Prove FR-007: a Beekeeper can flag an Answer as wrong or misleading, and that flag is retained as evaluation evidence. Slices 0001–0004 built the read path (retrieval, jurisdiction isolation, no-grounding behaviour, provenance); this is the first slice to give the Beekeeper a write path back into the system.

## Source Inputs

- FR-007 (user corrections)
- Decision log: Correction Trust Level For V1 (already resolved — every Correction is trusted directly, no review gate) and User Corrections Mechanism (this slice)
- `architecture/domain-model.md`: `Correction` entity (fields, v1 statuses, the `review_*` statuses reserved but not exercised)

## User Path

Given a dev-authenticated Beekeeper with a Workspace Membership, viewing any Answer (regardless of its grounding status)
When the Beekeeper flags the Answer as wrong or misleading and provides an explanation
Then the system records a Correction — workspace-scoped, tied to that Answer, with status `trusted` — and the Beekeeper sees an acknowledgment
And the Beekeeper may flag the same Answer again later, with new or additional notes

## Preconditions

- Same dev-authenticated User context and Workspace Membership as prior slices — no change.
- At least one Answer must already exist to flag (produced via the existing `POST /queries` flow).

## End-To-End Behaviour

Every `AnswerView`, regardless of `grounding_status`, offers a "Flag as wrong" control. Activating it reveals a required notes field. Submitting posts to a new endpoint, which:

- Confirms the requesting User has an active Workspace Membership for the given `workspace_id` (same check as `POST /queries`).
- Confirms the given `answer_id` actually belongs to that Workspace (via its parent Query) — otherwise 404, not 403, since the answer may not exist at all from the caller's perspective.
- Rejects empty notes (422) — enforced as a required field, not a soft warning.
- Inserts a `Correction` row with `status = 'trusted'` directly — v1 has no review gate, so there is no observable intermediate state.
- Returns an acknowledgment; the Beekeeper can submit another Correction for the same Answer later without restriction.

## Layers Touched

- Web UI: `AnswerView` gains a "Flag as wrong" control, a notes input, and a submitted acknowledgment, available on every grounding state.
- Core API (Advisor Service): new `POST /corrections` endpoint; new `CorrectionRepository` (save, and validate an Answer belongs to a Workspace); no changes to the existing query/answer workflow.
- Storage: new `corrections` table (`id`, `workspace_id`, `answer_id`, `created_by_user_id`, `notes`, `status`, `created_at`), matching the domain model's `Correction` entity. `status` defaults to `trusted`.
- Contracts: new `POST /corrections` request (`workspace_id`, `answer_id`, `notes`) and response (`id`, `answer_id`, `status`).
- Queue or async boundary: Not touched.
- Observability: Not touched.

## Test Seams

- Seam: `CorrectionRepository`. Behaviour verified: a Correction is persisted with the given notes and `status = 'trusted'`; a lookup correctly reports whether a given Answer belongs to a given Workspace (via its parent Query). Test style: integration test against a real Postgres test database.
- Seam: `POST /corrections` endpoint. Behaviour verified: a valid request persists a Correction and returns it; a request for a Workspace the User isn't an active member of is rejected (403); a request for an Answer that doesn't belong to the given Workspace is rejected (404); a request with empty notes is rejected (422); submitting twice for the same Answer succeeds both times. Test style: API-level test via `TestClient`, extending the pattern in `test_query_submission_slice.py`.
- Seam: End-to-end web UI workflow. Behaviour verified: flagging an Answer (including an ungrounded one) shows a notes field, submitting it shows an acknowledgment. Test style: Playwright + Gherkin.

## Data Shape

- New table: `corrections` (`id` uuid PK, `workspace_id` uuid NOT NULL REFERENCES workspaces, `answer_id` uuid NOT NULL REFERENCES answers, `created_by_user_id` uuid NOT NULL REFERENCES users, `notes` text NOT NULL, `status` text NOT NULL DEFAULT 'trusted', `created_at` timestamptz NOT NULL DEFAULT now()).
- No changes to `answers`, `queries`, or `citations`.

## Out Of Scope

- The `review_pending`/`review_approved`/`review_rejected` statuses — reserved in the domain model, not exercised; every v1 Correction goes straight to `trusted`, per the already-resolved Correction Trust Level decision.
- Any Corpus Curator-facing view for reading submitted Corrections — this slice only covers submission, not consumption or reporting. A future slice, not this one.
- Any automatic effect on a Corpus Document or Passage — a Correction is evaluation evidence only, per the domain model's explicit rule; it never edits the corpus itself.
- A structured "reason" taxonomy alongside notes — free-text only, per the grilled decision.

## Acceptance Criteria

- [x] A Beekeeper can submit a Correction (notes + implicit answer/workspace context) for any Answer, regardless of its `grounding_status`.
- [x] The Correction is persisted with `status = 'trusted'` and is workspace-scoped.
- [x] Submitting a Correction for a Workspace the User isn't an active member of is rejected (403).
- [x] Submitting a Correction for an Answer that doesn't belong to the given Workspace is rejected (404).
- [x] Submitting a Correction with empty notes is rejected (422).
- [x] A Beekeeper can submit more than one Correction for the same Answer.
- [x] The web UI offers the flag control on every Answer and shows an acknowledgment after submission.

## Open Questions

None — all four open questions (which Answers can be flagged, whether notes are required, whether repeat Corrections are allowed, whether a reason taxonomy is needed) were resolved via grilling before this doc was written; see the decision log entry above.
