# Domain Model Diagram

Visual companion to `architecture/domain-model.md`. Kept conceptual — attributes are limited to what orients the reader, not a full schema.

## Core Product And Governance Model

```mermaid
erDiagram
    WORKSPACE ||--o{ WORKSPACE_MEMBERSHIP : has
    USER ||--o{ WORKSPACE_MEMBERSHIP : holds
    USER ||--o{ INTERNAL_CAPABILITY : may_have

    WORKSPACE ||--o{ QUERY : owns
    WORKSPACE ||--o{ DATA_DELETION_REQUEST : may_have
    QUERY ||--|| ANSWER : produces
    ANSWER ||--o{ CITATION : has
    ANSWER ||--o{ CORRECTION : may_have
    ANSWER ||--o{ SOURCE_CONFLICT : may_flag
    ANSWER }o--|| ANSWER_GENERATION_VERSION : produced_by

    JURISDICTION ||--o{ CORPUS_DOCUMENT : has
    CORPUS_DOCUMENT ||--o{ PASSAGE : contains
    CORPUS_DOCUMENT |o--o| CORPUS_DOCUMENT : superseded_by
    PASSAGE ||--o{ CITATION : cited_by

    WORKSPACE {
        id id
        string display_name
        string status
    }
    USER {
        id id
        string display_name
        string status
    }
    WORKSPACE_MEMBERSHIP {
        id id
        id user_id
        id workspace_id
        string role
    }
    INTERNAL_CAPABILITY {
        id id
        id user_id
        string capability
    }
    JURISDICTION {
        id id
        string code
        string status
    }
    CORPUS_DOCUMENT {
        id id
        id jurisdiction_id
        string licence_terms
        string status
        id superseded_by_id
    }
    PASSAGE {
        id id
        id corpus_document_id
        string text_content
    }
    QUERY {
        id id
        id workspace_id
        string text
        id resolved_jurisdiction_id
    }
    ANSWER {
        id id
        id query_id
        string grounding_status
        id answer_generation_version_id
    }
    CITATION {
        id id
        id answer_id
        id passage_id
    }
    SOURCE_CONFLICT {
        id id
        id answer_id
        string description
    }
    CORRECTION {
        id id
        id workspace_id
        id answer_id
        string status
    }
    ANSWER_GENERATION_VERSION {
        id id
        string embedding_model
        string generation_model
        string prompt_template_version
        string corpus_snapshot_reference
    }
    DATA_DELETION_REQUEST {
        id id
        id workspace_id
        id requester_id
        string status
        datetime requested_at
        datetime completed_at
    }
```

## Reading Notes

- `CORPUS_DOCUMENT |o--o| CORPUS_DOCUMENT : superseded_by` is a self-reference: a document may point to the one document that superseded it. Optional on both sides because most documents are never superseded, and a document cannot supersede itself.
- `QUERY ||--|| ANSWER` is one-to-one for v1: one Query produces exactly one Answer. Follow-up questions are new Queries, not a thread, until conversational history is deliberately designed (see the domain model's Open Architecture Questions).
- `CORRECTION` and `SOURCE_CONFLICT` both hang off `ANSWER`, not off `QUERY` or `CITATION` — a correction is about whether the answer was right; a conflict is about whether the sources agreed. Keeping them separate keeps each one asking a single question.
- `ANSWER_GENERATION_VERSION` is deliberately not shaped like HiveSight's `Model Version` — there is no training/benchmark lifecycle behind it in v1, just a record of which embedding model, generation model, prompt template, and corpus snapshot produced a given answer, so a bad answer can be traced to its cause.
- `Workspace` here owns `Query`/`Answer`/`Correction`, not apiaries, hives, or inspections — deliberately parallel in shape to HiveSight's `Workspace`, different in content, per `CONTEXT.md`.
- `DATA_DELETION_REQUEST` is reserved, not operational — no v1 workflow reaches it. It exists now so a future retention/deletion policy is implementation work against an existing shape, not a schema redesign (see `requirements/decision-log.md`, Retention And Deletion Planning). It only touches Workspace-owned data (`Query`, `Answer`, `Citation`, `Correction`); `Corpus Document` and `Passage` are shared, not Workspace-owned, and are out of its scope by construction.
