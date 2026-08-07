# Vertical Slice 0013: Guest Access And Rate Limiting

## Purpose

Let a Beekeeper ask Varroa questions without signing in (frictionless trial for a prospect), while capping the real, per-request cost exposure (a Voyage embedding call plus a Claude generation call, both paid, per query) that an unauthenticated, unthrottled endpoint would otherwise expose to unlimited anonymous traffic once deployed publicly.

## Source Inputs

- `requirements/roadmap.md`, "Real user authentication" (Compliance and trust) — the parent item this was split out of.
- Grilled 2026-08-07: guest access is allowed (not gated behind sign-in), but must be rate-limited — a genuine cost/friction trade-off, decided directly by the user rather than defaulted.
- Grilled 2026-08-07: rate-limit key is IP address; exceeded behaviour is a hard block (429) with a sign-in-prompt message; starting limit is 10 queries/hour/IP.
- Grilled 2026-08-07: guest queries write into a single well-known shared Guest Workspace, not an ephemeral per-visitor Workspace or a new no-Workspace path — keeps `CONTEXT.md`'s "Workspace is the ownership boundary for queries/answers/corrections" invariant intact with no new concept.
- Grilled 2026-08-07: split from real Google OIDC sign-in, which becomes its own future slice with its own grilling pass — this slice is fully buildable and demoable without any OIDC work.
- `requirements/requirements.md` FR-000 (Workspace/Workspace Membership modelling) and `CONTEXT.md`'s `Workspace`/`User` definitions.

## User Path

Given a Beekeeper visits the Advisor web app without signing in
When they ask up to 10 Varroa questions within an hour
Then each question is answered normally, grounded in the corpus as today

Given a Beekeeper has already asked 10 questions within the last hour, without signing in
When they ask an 11th question
Then they see a message that they've reached the guest limit for this hour, with no new Answer generated

## Preconditions

- None — this is specifically the no-login path. (Today's dev-header mechanism on `/queries` is not real authentication either — every current web visitor already silently shares one hardcoded dev identity with no rate limiting at all. This slice makes that reality honest: `/queries` becomes genuinely unauthenticated, with IP-based rate limiting replacing the dev-header as the only access control.)

## End-To-End Behaviour

1. `POST /queries` drops the `x-dev-user-id` header requirement and the `workspace_id` request field. The request body becomes `{jurisdiction_id, text}` only.
2. A new `RateLimiterDep` FastAPI dependency checks the caller's IP (via `request.client.host`, honouring `X-Forwarded-For` since Fly.io deployment — still on the roadmap, not live yet — sits behind a proxy) against an in-memory fixed-window counter. Over the limit → `429` with a machine-readable reason the frontend can render as a sign-in-prompt message.
3. Under the limit → the request proceeds exactly as `/queries` does today, but resolves to a new well-known `GUEST_WORKSPACE_ID`/`GUEST_USER_ID` (analogous to today's hardcoded dev IDs, but now genuinely representing "no login," not a placeholder for missing auth) instead of a client-supplied `workspace_id`.
4. The web app drops `devUserId`/`workspaceId` from `submitQuery`'s request; on a `429` response, shows a guest-limit-reached message (plain text for now — this slice does not build real sign-in, so the message cannot yet link anywhere; the future OIDC slice upgrades it to a real "Sign in" call to action).
5. `/corrections` (flagging a wrong Answer) is explicitly untouched by this slice — see Out Of Scope.

## Layers Touched

- Web UI: `App.tsx`, `advisorApiClient.ts` (drop `devUserId`/`workspaceId` from the query call), a new guest-limit-reached message in the query form.
- Core API: `/queries` router — drops `DevUserIdDep`/`workspace_id`, adds `RateLimiterDep`; new `429` response shape.
- Analysis Service: Not touched — `AnswerQueryWorkflow` still just needs a `workspace_id`, now always the well-known Guest Workspace for this path.
- Storage: new seed data (well-known Guest User + Guest Workspace + Membership rows), same shape as today's dev seed rows — no schema change.
- Queue or async boundary: Not touched.
- Contracts: Not touched — `/queries` is Advisor's own internal web-facing endpoint, not a previously-declared external surface (unlike `/integrations/hivesight/*`), so this breaking change to its request shape doesn't need the external-contract grilling gate.
- Observability: the 429 path should be visible in whatever logging exists today (currently just default uvicorn access logs) — no new observability infrastructure built here.

## Test Seams

- Seam: `RateLimiter` (new) — an injectable component with an `allow(key: str) -> bool` seam, backed by an in-memory fixed-window counter with an injectable clock (not `time.time()` directly) so tests don't need to sleep for real.
  Behaviour verified: allows up to the configured limit within the window; blocks the next request; a different key (IP) is unaffected by another key's usage; a request after the window elapses (simulated via the injected clock) is allowed again.
  Test style: pytest, unit-level, no database.
- Seam: `POST /queries` router
  Behaviour verified: 11th request from the same IP within the window returns 429 with a reason; a request from a different IP is unaffected; a within-limit request behaves exactly as today (grounded Answer, citations) but with no auth header required.
  Test style: pytest, `TestClient`, using a small test-configured limit (not the real 10/hour) for speed — limit and window become environment-configurable settings, following this project's existing pattern for environment-configurable, test-vs-real values (e.g. the grounding thresholds).
- Seam: Web acceptance (Gherkin) — **descoped during implementation for the exceeded-limit behaviour specifically, see note below.** The normal under-limit path needed no new scenario: every existing scenario already asks a question with no auth header (this slice's own change), so guest querying is already exercised by the full existing suite.

## Data Shape

- `GUEST_USER_ID` / `GUEST_WORKSPACE_ID`: new well-known UUID constants, seeded the same way today's `DEV_USER_ID`/`DEV_WORKSPACE_ID` are.
- `RateLimiterSettings` (new, environment-configurable): `guest_rate_limit` (default 10), `guest_rate_limit_window_seconds` (default 3600).
- `POST /queries` request: `{jurisdiction_id: UUID, text: str}` — `workspace_id` removed.
- `POST /queries` 429 response: `{detail: {reason: "guest_rate_limit_exceeded", message: str}}` — nested under `detail` per FastAPI's standard `HTTPException` shape, rather than a flat top-level field, since that needs no new exception-handler plumbing.

## Out Of Scope

- Real Google OIDC sign-in — its own future slice, with its own grilling pass (OAuth callback flow, session storage, frontend sign-in UI, migrating every currently-dev-header-gated authenticated route).
- `/corrections` (flagging a wrong Answer) — stays exactly as it is today, still behind the existing dev-header mechanism. It doesn't call any paid external API (pure DB write), so the cost-exposure motivation for this slice doesn't apply to it, and gating it behind sign-in now would regress an already-working feature (Slice 0005) ahead of real sign-in actually existing.
- Multi-instance-correct rate limiting (e.g. Redis-backed, shared across processes). The in-memory counter is correct for a single-instance deployment, which is what exists today and is what's actually planned for the near-term Fly.io rollout; if/when the service scales to multiple instances, per-instance limits under-enforce the true global limit — a known, explicitly-flagged limitation, not a silent gap.
- `/integrations/hivesight/*` — already gated by `HiveSightServiceAuthDep` (machine-to-machine, not a guest browser session); this slice does not touch it.
- Any product/UX design for the eventual "sign in" call to action — the 429 message is plain text for now, since there is nowhere real to send someone to sign in yet.

## Acceptance Criteria

- [x] A guest (no auth header) can ask up to the configured limit of questions per hour per IP, answered exactly as today.
- [x] The next request over the limit from the same IP returns 429 with a guest-limit-reached reason, and generates no Answer.
- [x] A different IP is unaffected by another IP's usage (proven at the `RateLimiter` unit seam).
- [x] `RateLimiter` unit tests cover allow/block/window-reset with an injected clock, no real sleeping.
- [x] `/corrections` is verified unchanged (still works exactly as before) — a regression check, not new behaviour. Also caught and fixed a real bug this slice introduced: the correction flow was still pointing at the old dev identity while the Answer it corrects now always belongs to the Guest Workspace, causing a 404 — fixed by pointing `AnswerView`'s correction submission at the Guest identity instead.
- [x] Traceability updated to reflect guest querying is now the default, unauthenticated path.

## Open Questions

None outstanding at design time — all real design forks (guest allowed at all, Workspace shape, rate-limit key, exceeded behaviour, limit size, split from OIDC) were grilled and resolved before writing this doc.

**Implementation-time finding**: the rate limiter is a process-wide singleton (correct per its own design — see Out Of Scope on multi-instance limits), and the acceptance suite's `webServer` is one shared process driven sequentially through every scenario in the file (`workers: 1`). A Gherkin scenario for "guest exceeds the limit" would either need an artificially tiny test limit (which then collides with every *other* scenario's own query traffic in the same run, since they share the same singleton and the same client IP) or a second, fully isolated Playwright config for one scenario — real added complexity for something two other seams already prove cleanly. Proved instead at: the `RateLimiter` unit tests (allow/block/reset), the `POST /queries` pytest test (`test_submit_query_beyond_the_guest_rate_limit_returns_429`, using a scoped dependency override so it doesn't touch the shared production singleton), and `advisorApiClient.test.ts` (the frontend correctly extracts and surfaces the 429's `detail.message`). Together these prove request-level blocking, HTTP-shape correctness, and client-side message handling — the three things that actually needed proving — without the shared-singleton test-isolation risk. The acceptance suite's `ADVISOR_API_GUEST_RATE_LIMIT` is set deliberately high (1000) precisely so normal suite traffic never approaches it.
