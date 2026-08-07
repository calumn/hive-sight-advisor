# HiveSight Advisor

HiveSight Advisor is a grounded knowledge and decision-support product for beekeepers managing Varroa mite risk. It answers a beekeeper's question with guidance drawn from a curated, multi-jurisdiction corpus of apicultural sources — never an uncited generation — with every claim traceable back to a source passage and citation.

It is architecturally independent of [HiveSight](https://github.com/calumn/hive-sight) (HiveSight's photo-based mite/bee detection product) but shares beekeeping domain territory with it, and follows the same SDLC discipline. See [`requirements/vision.md`](requirements/vision.md) for the full product vision and [`CONTEXT.md`](CONTEXT.md) for domain language.

**Current status**: 14 vertical slices built (grounded Q&A, jurisdiction isolation, no-grounding honesty, source supersession, user corrections, corpus curator tooling, treatment trade-off comparison, an agentic LangGraph treatment-plan workflow integrating with HiveSight, Voyage retry/backoff, passage chunking, guest access with rate limiting, and real Google OIDC sign-in). See [`requirements/roadmap.md`](requirements/roadmap.md) for what's next, [`requirements/decision-log.md`](requirements/decision-log.md) for why things are the way they are, and `architecture/vertical-slice-*.md` for each slice's own design doc.

## Structure

- `apps/web`: web UI — Query input with Jurisdiction selector, Answer display with Citation.
- `services/advisor-api`: the Advisor Service — retrieval, embedding, generation, and persistence for grounded query answering.
- `scripts`: local dev tooling (server up/down, database seed script).
- `architecture`: architecture decisions, domain model, and vertical slice plans.
- `requirements`: vision, requirements, and decision log.

## Clean Machine Setup

Install these prerequisites first:

- Python 3.12
- Node.js 20 or newer
- pnpm
- Docker Desktop, for local Postgres (with the `pgvector` extension)

On macOS with Homebrew, that is typically:

```sh
brew install python@3.12 node pnpm
```

From a fresh clone, install dependencies from the repo root:

```sh
cd ~/Projects/hive-sight-advisor
python3.12 -m venv .venv-advisor-api
cd services/advisor-api
../../.venv-advisor-api/bin/pip install -e ".[dev]"
cd ../..
pnpm install
```

Start Docker Desktop before bringing up Postgres.

### API keys

Copy the example env file into the (gitignored) real one, then fill in real values:

```sh
cp .env.example services/advisor-api/.env
```

You'll need:

- `VOYAGE_API_KEY` — for embeddings
- `ANTHROPIC_API_KEY` — for Claude generation

Never commit `services/advisor-api/.env` or paste real keys into `.env.example` — the example file is tracked by git and must only ever contain placeholders.

## Daily Local Start

Start local Postgres (only needed once — it keeps running across restarts):

```sh
pnpm db:up
```

Apply migrations and seed the dev corpus (a hand-picked UK Varroa source document, embedded for real via Voyage AI):

```sh
pnpm db:migrate
pnpm db:seed
```

Start both servers:

```sh
pnpm dev:all
```

This runs in the foreground and streams both servers' logs — press `Ctrl+C` to stop them cleanly. If you want your terminal back immediately, run `pnpm dev:all &` instead.

Open the web UI at:

```text
http://localhost:5183
```

Check whether the servers are already running:

```sh
pnpm dev:status
```

Stop the servers:

```sh
pnpm dev:stop
```

Stop Postgres (optional — leave it running between sessions if you'd rather not re-seed):

```sh
pnpm db:down
```

`pnpm dev:all` starts the Advisor API on `http://127.0.0.1:8010` and the web UI on `http://127.0.0.1:5183`. These are deliberately different ports from HiveSight's own `8000`/`5173`, so both projects' dev servers can run side by side.

## Tests

Run the Python test suite from `services/advisor-api`:

```sh
cd services/advisor-api
../../.venv-advisor-api/bin/python -m pytest -v
```

Live provider contract tests (real Voyage/Claude calls) are skipped by default and only run if `VOYAGE_API_KEY`/`ANTHROPIC_API_KEY` are set in the environment — see [`requirements/decision-log.md`](requirements/decision-log.md), "Slice 0001 Test And Seed Approach".
