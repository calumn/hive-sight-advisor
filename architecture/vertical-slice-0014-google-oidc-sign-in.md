# Vertical Slice 0014: Google OIDC Sign-In

## Purpose

Let a Beekeeper sign in with their Google account, replacing the dev-header placeholder with a real, accountable identity — and require that identity to flag a Correction, since Corrections are trusted directly (FR-007) with no review gate.

## Source Inputs

- `requirements/roadmap.md`, "Real user authentication" — the remaining piece after Slice 0013 split guest access/rate limiting out.
- Direction already agreed 2026-08-07 (pre-slice discussion): Google as identity provider (matching HiveSight's own independent plan), independent sessions per app (not true SSO), Google `sub` as the `User` anchor from day one.
- Grilled 2026-08-07: Google Identity Services (GIS) JS SDK for sign-in, not a server-side OAuth Authorization Code+PKCE flow — Advisor only needs identity, never calls a Google API on the user's behalf, so a backend callback route would be unused complexity.
- Grilled 2026-08-07: session carried as a Bearer token (the Google ID token itself, resent by the frontend), not a cookie — the backend's CORS config doesn't currently allow credentials, and cross-origin cookies need setup this app has no other reason to add yet.
- Grilled 2026-08-07: no custom session minting — the backend verifies Google's own ID token directly (local signature check against Google's cached public keys) rather than issuing its own longer-lived session JWT. GIS handles silent refresh in the browser while the tab is open.
- Grilled 2026-08-07: `/corrections` now requires real sign-in — Guests can still ask questions, but flagging a wrong Answer as trusted evidence now requires an accountable identity.
- `CONTEXT.md`'s `User`/`Workspace Membership` definitions; `requirements/requirements.md` FR-000, FR-007.

## User Path

Given a Beekeeper visits the Advisor web app
When they click "Sign in with Google" and complete Google's sign-in prompt
Then they see themselves signed in, and can flag a Correction on an Answer using their own accountable identity

Given a Beekeeper is not signed in
When they try to flag a Correction
Then they're prompted to sign in first, rather than the flag silently failing or being submitted anonymously

## Preconditions

- **External, not buildable from this repo alone**: a Google Cloud OAuth 2.0 Client ID (Web application type) must exist, with the dev/deployed origins registered as authorized JavaScript origins. This is a Google Cloud Console action the user needs to take (parallels the Voyage/Anthropic API key precondition from earlier slices) — the resulting Client ID is public (not a secret) and goes into `VITE_GOOGLE_CLIENT_ID`.
- Guest querying (Slice 0013) is otherwise unaffected — `/queries` continues to work with no sign-in.

## End-To-End Behaviour

1. The web app loads Google's GIS script and renders a "Sign in with Google" button (`QueryForm` area or a new header). On success, GIS hands the frontend a signed Google ID token (a JWT) directly — no backend redirect involved.
2. The frontend holds this token in memory (not persisted across a page reload beyond GIS's own silent-refresh behavior) and sends it as `Authorization: Bearer <token>` on `/corrections` requests. `workspace_id` is dropped from the `/corrections` request body — the backend resolves the caller's own Workspace from the verified token, mirroring how `/queries` already resolves the Guest Workspace server-side (Slice 0013).
3. A new `GoogleIdTokenVerifier` component verifies the token's signature (against Google's cached public JWKS), issuer, audience (must match `VITE_GOOGLE_CLIENT_ID`'s server-side counterpart), and expiry — using the official `google-auth` library, not a hand-rolled JWT check.
4. On first sight of a given Google `sub`, the backend auto-provisions a `User` (with `google_sub`, `email`, `display_name` from the token's claims) and a personal `Workspace` + owner `Workspace Membership`, transactionally — the same "provision on first use" pattern already used for the Dev and Guest identities, just triggered by a real external identity instead of a hardcoded seed row. On a returning `sub`, the existing `User`/`Workspace` is looked up, not recreated.
5. `/corrections` without a valid Bearer token returns 401; the frontend shows a "sign in to flag this" prompt instead of the correction form.
6. `/queries` gains an *optional* Bearer token: if present and valid, the query resolves to the signed-in user's own Workspace and skips the guest rate limiter entirely (a real, accountable identity replaces the reason the limiter exists); if absent, behaves exactly as Slice 0013 built it (Guest Workspace, rate-limited).

## Layers Touched

- Web UI: new `SignInButton`/`useGoogleSignIn` piece loading the GIS script; `App.tsx` tracks signed-in state; `AnswerView`'s correction form is gated on it.
- Core API: `/corrections` — drops `workspace_id`, gains required Bearer auth; `/queries` — gains *optional* Bearer auth (guest path unchanged when absent).
- Analysis Service: Not touched.
- Storage: migration adds `google_sub` (unique, nullable), `email`, `display_name` to `users` — `display_name` already exists (unused so far); `google_sub`/`email` are new. No change to `workspace_memberships`.
- Queue or async boundary: Not touched.
- Contracts: Not touched — `/queries` and `/corrections` are Advisor's own internal endpoints, not previously-declared external surface.
- Observability: Not touched — same as prior slices, no new logging infrastructure.

## Test Seams

- Seam: `GoogleIdTokenVerifier` (new)
  Behaviour verified: a validly-signed token with matching audience/issuer/expiry is accepted and its claims (`sub`, `email`, `name`) extracted; wrong audience, wrong issuer, and expired-token cases are all rejected. Verified against real Google-signed test tokens is not practical in CI — this seam is tested against a locally-signed JWT using a test keypair, with the verifier's trusted-JWKS-fetch step injected/stubbed, so the test proves the verification *logic* without a live Google dependency.
  Test style: pytest, unit-level.
- Seam: `UserProvisioningRepository` (new, or a method on an existing repository)
  Behaviour verified: first sight of a `sub` creates exactly one `User` + `Workspace` + owner `Membership`; a second call with the same `sub` returns the existing set unchanged (no duplicate rows).
  Test style: pytest, real test-database transaction.
- Seam: `POST /corrections` router
  Behaviour verified: missing/invalid Bearer token → 401; valid token → correction saved against the caller's own (possibly newly-provisioned) Workspace.
  Test style: pytest, `TestClient`, with `GoogleIdTokenVerifier` swapped for a deterministic fake via dependency override (mirrors the existing `HiveSightServiceAuthDep`/`RateLimiterDep` override pattern).
- Seam: `POST /queries` router
  Behaviour verified: a valid Bearer token resolves to the signed-in user's Workspace and is not rate-limited even past the guest limit; no token behaves exactly as Slice 0013 (regression check).
  Test style: pytest, `TestClient`.
- Seam: Web acceptance (Gherkin) — the sign-in button itself talks to real Google infrastructure (GIS), which the acceptance suite's stub-provider, no-external-calls philosophy deliberately avoids elsewhere. Real sign-in end-to-end is verified manually in a live browser pass per slice (same as every other slice's real-AI-behaviour caveat), not via Playwright — driving Google's actual consent screen from an automated test is neither practical nor something this project should depend on for CI. What *is* Gherkin-testable: the "not signed in → prompted to sign in, not silently blocked" UI behavior, using a fake/stubbed sign-in state rather than driving real Google infrastructure.
  Test style: Playwright + Gherkin for the "prompted to sign in" case only; everything upstream of "a valid token exists" is proven at the pytest seams above plus a manual live pass.

## Data Shape

- `users` migration: `ALTER TABLE users ADD COLUMN google_sub text UNIQUE, ADD COLUMN email text;` (`display_name` already exists).
- `POST /corrections` request: `{answer_id: UUID, notes: str}` — `workspace_id` removed.
- `POST /queries` request: unchanged shape (`{jurisdiction_id, text}`); Bearer token now optional via the `Authorization` header, not the body.
- `VITE_GOOGLE_CLIENT_ID` (new frontend env var, public); backend needs the same Client ID (as the expected token audience) via a new `google_client_id` setting.

## Out Of Scope

- True SSO / shared session between HiveSight and Advisor — independent sessions per app, already decided in the pre-slice discussion.
- A "my Corrections history" or any other authenticated-only view — this slice only makes the *identity* real, not new user-facing features built on top of it.
- Backend-minted long-lived sessions (e.g. refresh tokens surviving a closed browser tab) — explicitly rejected in grilling; relies on GIS's own in-tab silent refresh.
- Signing out (a "sign out" affordance) — not grilled, likely small, but not required to prove the core behaviour; flagged as a gap to close before this ships broadly, not before this slice is "done."
- Migrating the internal `Internal Capability` / Corpus Curator CLI auth path — that's a separate, already-working mechanism (API keys via `.env`), untouched by this slice.
- Any change to how the Guest identity or rate limiting work — Slice 0013's behaviour is extended (optional token), not altered.

## Acceptance Criteria

- [x] `GoogleIdTokenVerifier` correctly accepts a validly-signed token and rejects wrong-audience/wrong-issuer/expired tokens.
- [x] First sign-in with a given `sub` provisions exactly one `User`/`Workspace`/`Membership`; a repeat sign-in reuses them.
- [x] `/corrections` rejects requests with no or invalid Bearer token (401) and accepts valid ones, saving the Correction against the caller's own Workspace.
- [x] `/queries` with a valid Bearer token resolves to the signed-in user's Workspace and bypasses the guest rate limit.
- [x] `/queries` with no token behaves exactly as Slice 0013 (regression check).
- [x] The frontend shows a real "Sign in with Google" button and gates the correction form on signed-in state.
- [ ] A manual live-browser pass confirms real Google sign-in end-to-end (not just the stubbed/mocked seams) — **blocked on the Google Cloud OAuth Client ID precondition**, not yet created. Everything else is built and tested; this is the one remaining step before the feature can be considered fully proven, not just mechanically correct.
- [x] Traceability and roadmap updated.

## Open Questions

None outstanding from grilling.

**Implementation-time finding**: the two pre-existing browser-level correction-submission scenarios (Slice 0005) could no longer be driven through the real UI once sign-in became required — Google's sign-in can't be automated in Playwright without either driving Google's real consent screen or adding a test-only auth bypass to the app itself. Grilled directly with the user: rejected the bypass (a real, if narrow, security-relevant code path added to production source, for test convenience) in favour of accepting the coverage move. The two scenarios were replaced with one scenario proving the sign-in gate itself (`user-corrections.feature`); full correction-submission behaviour (success, duplicate, wrong-workspace, no-auth, invalid-token) remains fully covered at the `POST /corrections` pytest/`TestClient` seam, just no longer through the browser. This is a real, deliberate reduction in browser-level coverage for previously-UI-provable behaviour — not silently dropped, but a genuine trade-off accepted in exchange for not adding auth-bypass code to the app.
