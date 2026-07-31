# Implementation Plan: Vertical Slice 0001

Companion to `architecture/vertical-slice-0001-grounded-query-answer-with-seeded-corpus.md`. This plan sequences the one-time scaffolding and the TDD red-green cycles needed to deliver that slice, per `sdlc-delivery-tdd`, `sdlc-delivery-python-service-style`, `sdlc-delivery-typescript-web-style`, and `sdlc-delivery-dependency-injection`.

Stack choices below follow HiveSight's own conventions where nothing in this project's architecture says otherwise (Python/FastAPI, pytest + pytest-bdd, ruff, pnpm + Vite/React/TS, Postgres) — consistent tooling costs nothing extra to learn and the two products remain architecturally independent regardless. Redis and MinIO are not carried over: there is no async job and no binary object storage in this architecture (Service Topology decision).

## Scaffolding (one-time, not TDD)

1. `services/advisor-api/` — Python service, `pyproject.toml` modelled on `hive-sight/services/core-api/pyproject.toml`: FastAPI, `psycopg[binary]`, `pgvector` (Python client bindings), `anthropic`, `voyageai`; dev extras `httpx`, `pytest`, `pytest-bdd`, `ruff`.
2. `apps/web/` — pnpm workspace member, Vite + React + TypeScript, modelled on `hive-sight/apps/web`.
3. `docker-compose.yml` — one `postgres` service using `pgvector/pgvector:pg16` (not plain `postgres:16`, since `pgvector` must be installed) with a healthcheck, matching HiveSight's compose shape otherwise.
4. Root `pnpm-workspace.yaml` / `package.json` if `apps/web` needs monorepo tooling; otherwise a plain `apps/web/package.json` is enough at this scale.
5. `.env.example` — `DATABASE_URL`, `VOYAGE_API_KEY`, `ANTHROPIC_API_KEY`, dev-auth header name, matching HiveSight's `.env.example` shape.
6. Typed settings object (`settings.py`) loaded once, per `sdlc-delivery-python-service-style` — no scattered `os.environ` reads.

None of this is itself a TDD cycle — it is infrastructure the first tracer bullet needs to exist.

## Module Layout

```
services/advisor-api/src/hive_sight_advisor_api/
  main.py                    # thin: app factory, router registration
  settings.py                # typed settings, loaded once
  dependencies.py            # FastAPI Depends: dev-auth user, workspace context, adapters
  routers/
    query.py                 # thin route handlers only
  workflows/
    answer_query.py           # deep module: retrieval + generation orchestration
  adapters/
    embedding_voyage.py       # production Voyage AI adapter
    embedding_stub.py         # deterministic stub for default test suite
    generation_claude.py      # production Claude adapter
    generation_stub.py        # documented fixture stub (Slice 0001 Test And Seed Approach decision)
  repositories/
    corpus_repository.py      # Corpus Document / Passage reads, pgvector similarity search
    query_repository.py       # Query / Answer / Citation writes
scripts/
  seed_slice_0001.py          # checked-in, rerunnable seed script (per decision log)
```

```
apps/web/src/
  api/advisorApiClient.ts     # single API client seam, per sdlc-delivery-typescript-web-style
  components/QueryForm.tsx    # Jurisdiction selector + Query input
  components/AnswerView.tsx   # Answer text + Citation display
  App.tsx
```

## Dependency Injection Seams

Per `sdlc-delivery-dependency-injection` — no interface until there are two real adapters or a clear near-term second one. Both seams below already have two adapters (production + stub), so both earn a Protocol now:

- `EmbeddingProvider` protocol: `embed_voyage.py` (production) and `embed_stub.py` (deterministic vector for tests). Injected via `Depends`.
- `GenerationProvider` protocol: `generation_claude.py` (production) and `generation_stub.py` (documented fixture, used in the default suite per the Slice 0001 Test And Seed Approach decision).
- `CorpusRepository` / `QueryRepository`: injected via `Depends`, backed by a real Postgres test database in integration tests (local-substitutable, per `sdlc-delivery-python-service-style` testing guidance) — not mocked.
- Dev-authenticated user / Workspace context: `Depends`, matching HiveSight's dev-auth header pattern exactly, with dependency overrides in tests rather than patched globals.

## TDD Sequence

One seam, one test, one minimal implementation per cycle — red before green, no anticipating later cycles.

1. **Health check.** `GET /health` returns 200. Thinnest possible tracer bullet to prove the scaffolding (FastAPI app, test client, CI) is wired end to end, matching HiveSight's own `test_health.py` convention. Not itself part of the slice's behaviour, but the cheapest way to catch a broken scaffold before writing real seams against it.
2. **Corpus repository / pgvector retrieval seam.** Given a seeded Passage with a known embedding and a query embedding close to it, `CorpusRepository.find_similar_passages(...)` returns the correct Passage. Integration test against a real Postgres/pgvector test database.
3. **Embedding adapter seam.** `EmbeddingProvider.embed(text)` returns a vector. Test the stub adapter's deterministic contract first; the Voyage adapter's contract test can be a separate, explicitly-marked live test (same reasoning as the Claude stub decision — avoid unnecessary spend/flakiness in the default suite).
4. **Generation boundary seam.** Given retrieved Passage(s), `GenerationProvider.generate_answer(query, passages)` returns Answer text plus a Citation referencing the correct Passage id. Test against `generation_stub.py` in the default suite.
5. **`answer_query` workflow (deep module).** Given a Query and Jurisdiction, orchestrates embed → retrieve → generate → persist, returns an `Answer` with `Citation`. Test through the workflow's public interface, with the repository and both providers injected as stubs/test doubles — this is the seam most worth testing thoroughly, per `sdlc-delivery-tdd`'s seam-selection guidance.
6. **Query submission API endpoint.** `POST /queries` — dev-authenticated request with valid Workspace Membership returns 200 with Answer + Citation; a request without valid membership is rejected. Integration test with dependency overrides and dev-auth headers, matching HiveSight's test style.
7. **Web API client seam.** `advisorApiClient.submitQuery(...)` — tested with mocked `fetch`, per `sdlc-delivery-typescript-web-style`.
8. **Web UI workflow.** `QueryForm` submits, `AnswerView` renders Answer + Citation, loading/ready/error states shown explicitly. Component/page-level test once this workflow is real.
9. **End-to-end acceptance test.** A `pytest-bdd` scenario (or Playwright, if the web layer is far enough along) walking the full User Path from the slice doc, matching HiveSight's `test_vertical_slice_NNNN_bdd.py` convention.

Steps 2–4 can happen in any order relative to each other since they are independent seams; 5 depends on all three; 6 depends on 5; 7–8 depend on 6; 9 depends on everything.

## Seed Script

`scripts/seed_slice_0001.py` — idempotent (safe to rerun), inserts one UK `Corpus Document` and its `Passage`(s) with real Voyage AI embeddings (not fabricated vectors, so retrieval is genuinely exercised). Checked in per the Slice 0001 Test And Seed Approach decision, reusable for slice 2's second jurisdiction.

## Out Of Scope For This Plan

Everything already marked Out Of Scope in the slice doc (ingestion pipeline, multi-jurisdiction blending, no-grounding path, corrections, real auth, observability). This plan sequences only the work inside Slice 0001's boundary.

## Closeout

Once implementation begins, log meaningful AI-SDLC observations as cycles complete rather than batching to the end, consistent with this project's stated practice.
