# Vertical Slice 0006: Corpus Curator CLI Tooling With AI-Assisted Review

## Purpose

Give the Corpus Curator persona (currently: hand-editing Python dataclasses in `scripts/seed_slice_0001.py` and re-running the whole seed script) a lighter, purpose-built way to add or retire a Corpus Document — without touching code, and without re-embedding the entire corpus for a single addition. Layered on top: an AI-assisted review step that gives the Curator an advisory signal on relevance and potential overlap/contradiction with existing corpus content, applying real judgement assistance to the manual, ingestion-time process the Source Supersession And Conflict Detection decision already committed to, rather than replacing it.

## Source Inputs

- Roadmap: "Internal Corpus Curator tooling" (Technical — Corpus management tooling)
- Decision log: Ingestion Trigger, Source Supersession And Conflict Detection (existing — manual, curator-led, ingestion-time judgement), Corpus Curator CLI Tooling And AI-Assisted Review (this slice)
- `architecture/domain-model.md`: Corpus Curator persona, `Corpus Document` entity (including the `retired` status, reserved but never exercised until now)

## User Path

Given a Corpus Curator with direct access to the database and a Voyage/Anthropic API key
When they run `python -m hive_sight_advisor_api.corpus_admin add-document` with a jurisdiction, title, source, licence terms, and a passage text file
Then the tool embeds the passage, retrieves the nearest existing passages in that jurisdiction, shows an AI-generated advisory on relevance and potential overlap/contradiction, and — after the Curator confirms — inserts the new Corpus Document and Passage into the database and records the addition in a source-controlled data file
And when they instead run `python -m hive_sight_advisor_api.corpus_admin retire-document` naming an existing document, the tool marks it `retired` in the database and records that retirement in the same source-controlled file, so a fresh seed run reproduces the corpus exactly as it stands today

## Preconditions

- A reachable Postgres database with the existing schema (no migration needed — `status = 'retired'` is already a valid value, just never used).
- `VOYAGE_API_KEY` and `ANTHROPIC_API_KEY` set (the tool has no stub-only mode; it is a real-content operation, not something exercised against fake providers in normal use — though the underlying providers are still built with real/stub adapters for testability, per the existing two-adapter rule).

## End-To-End Behaviour

`add-document`:
1. Resolve the given jurisdiction code to a `Jurisdiction` row (error if not found — no silent jurisdiction creation).
2. Embed the given passage text via `EmbeddingProvider`.
3. Retrieve the nearest existing Passages in that Jurisdiction via `CorpusRepository.find_similar_passages` (a handful, not just one).
4. Call `CorpusReviewProvider.review_candidate` with the candidate text, jurisdiction, and those nearby Passages. It returns free-text advisory prose covering topic/jurisdiction relevance and any apparent overlap or contradiction with what's already there — **advisory only, never a pass/fail gate**, consistent with the Correction Trust Level For V1 reasoning (one real curator, who is the domain expert; a gate would just be self-review).
5. Print the advisory, then prompt for confirmation before writing anything (skippable via a `--yes` flag for non-interactive use).
6. On confirmation: insert the Corpus Document and Passage rows into the database, and append the new document's full definition to `scripts/curator_added_documents.yaml`.

`retire-document`:
1. Resolve the named document (by title or id).
2. Update its status to `retired` in the database.
3. Append its id to the same YAML file's `retired_document_ids` list.

`scripts/seed_slice_0001.py`'s `seed()` function is extended to also load `curator_added_documents.yaml` after seeding its existing hardcoded documents: insert every listed document/passage, then apply every listed retirement — regardless of whether the retired document originated from the Python-hardcoded baseline or from a prior curator addition. This keeps the *entire* corpus (baseline plus every curator action) reproducible from a fresh clone, the same property every other part of this project's data already has.

## Layers Touched

- Core API (Advisor Service) package: new `CorpusReviewProvider` protocol and two adapters (`StubCorpusReviewProvider`, `ClaudeCorpusReviewProvider`), matching the existing `EmbeddingProvider`/`GenerationProvider` two-adapter pattern.
- Core API package: new `hive_sight_advisor_api/corpus_admin.py` — placed inside the installed package rather than `scripts/`, matching `db.py`'s existing precedent for operational CLI tooling with argparse (invoked via `python -m`), which also makes its core logic importable by pytest with no path workarounds. Its core `add_document`/`retire_document` logic is written as plain testable functions taking explicit dependencies, with a thin argparse/interactive wrapper on top — the same separation of concerns the rest of this codebase already uses between route handlers and workflows.
- Scripts: `scripts/seed_slice_0001.py` gains a step to load and apply `scripts/curator_added_documents.yaml` (the data file itself stays in `scripts/`, alongside the seed script that consumes it, since it's data rather than an operational tool).
- Storage: no schema change. Uses the existing `status = 'retired'` value for the first time.
- Data: new `scripts/curator_added_documents.yaml`, source-controlled, holding curator-added document definitions and a list of retired document ids.
- Web UI: Not touched.
- Contracts: Not touched — this is operator tooling, not an API surface.

## Test Seams

- Seam: `StubCorpusReviewProvider`. Behaviour verified: deterministic advisory text reflecting whether nearby passages were supplied, usable in tests without a live Claude call. Test style: unit test.
- Seam: `corpus_admin.add_document`/`retire_document` core functions. Behaviour verified: `add_document` inserts a correctly-populated Corpus Document and Passage and appends the correct entry to a given YAML file path; `retire_document` updates status and appends to `retired_document_ids`; retiring a nonexistent document raises a clear error rather than silently doing nothing. Test style: integration test against a real Postgres test database with a temporary YAML file path, using the stub embedding/review providers — extending the established pattern from `test_corpus_repository.py`/`test_correction_repository.py`.
- Seam: `seed()`'s new load-and-apply step for `curator_added_documents.yaml`. Behaviour verified: a document listed in the YAML file is seeded correctly; a document id listed under `retired_document_ids` ends up `retired` regardless of whether it came from the Python-hardcoded baseline or the YAML file. Test style: integration test with a temporary YAML fixture file.
- Seam: `ClaudeCorpusReviewProvider`. Behaviour verified (live, not in the default suite): given a candidate document and nearby passages, produces non-empty advisory text. Test style: live contract test skipped without `ANTHROPIC_API_KEY`, matching `test_generation_claude_live.py`'s existing pattern.

## Data Shape

- New file: `scripts/curator_added_documents.yaml`:
  ```yaml
  documents:
    - id: "<uuid>"
      jurisdiction_code: "uk"
      title: "..."
      source: "..."
      source_url: "..."
      licence_terms: "..."
      passage_id: "<uuid>"
      passage_text: "..."
  retired_document_ids:
    - "<uuid>"
  ```
- New dependency: `pyyaml`, added to `services/advisor-api/pyproject.toml`'s main dependencies (available in the same venv the seed script and this tool already run in).
- No database schema changes.

## Out Of Scope

- HTTP admin endpoints — a CLI script only, per the grilled decision (avoids inventing a corpus-admin access-control model that doesn't otherwise exist).
- Updating an existing document's text/metadata, or marking supersession, via this tool — still done by hand-editing `seed_slice_0001.py`'s existing dataclasses for now, per the grilled v1 scope decision. Natural follow-ups once this tool's shape has proven itself.
- The review step gating or blocking anything — advisory only, per the grilled decision.
- The review step judging factual/scientific accuracy of treatment claims — it judges relevance and apparent overlap/contradiction with existing content only; the Curator's own domain judgement remains authoritative on correctness.
- Passage chunking (splitting one long source document into multiple Passages) — this tool assumes one Passage per Corpus Document, matching every document in the corpus today. A separate, already-tracked roadmap item.
- End-user (Beekeeper-facing) document suggestion — a different, larger future item (needs its own trust/review-gate model, since a bad addition there would affect every user, not just a trusted internal operator). Tracked separately in the roadmap.

## Acceptance Criteria

- [x] `python -m hive_sight_advisor_api.corpus_admin add-document` embeds the candidate passage, shows an AI-generated advisory (relevance + overlap/contradiction against nearby existing Passages in the same Jurisdiction), and — on confirmation — inserts the new Corpus Document/Passage and records it in `curator_added_documents.yaml`.
- [x] The advisory never blocks adding the document; the Curator's confirmation is what decides.
- [x] `python -m hive_sight_advisor_api.corpus_admin retire-document` marks an existing document `retired` in the database and records the retirement in the same YAML file.
- [x] `seed_slice_0001.py`'s `seed()` function loads `curator_added_documents.yaml` and reproduces the same corpus state (added documents present, retired documents retired) on a fresh database.
- [x] Retiring a document that originated from the Python-hardcoded baseline works the same way as retiring one added via the CLI tool.

## Open Questions

None — all seven open questions (what the review checks, advisory vs. blocking, whether the review compares against existing corpus content, CLI vs. HTTP admin API, whether to persist to a source-controlled file, which file format, and v1 operation scope) were resolved via grilling before this doc was written; see the decision log entry above.
