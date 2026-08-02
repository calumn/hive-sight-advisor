CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS jurisdictions (
    id uuid PRIMARY KEY,
    code text NOT NULL UNIQUE,
    display_name text NOT NULL,
    status text NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS corpus_documents (
    id uuid PRIMARY KEY,
    jurisdiction_id uuid NOT NULL REFERENCES jurisdictions(id),
    title text NOT NULL,
    source text NOT NULL,
    licence_terms text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    superseded_by_corpus_document_id uuid REFERENCES corpus_documents(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS passages (
    id uuid PRIMARY KEY,
    corpus_document_id uuid NOT NULL REFERENCES corpus_documents(id),
    text_content text NOT NULL,
    position integer NOT NULL DEFAULT 0,
    embedding vector(1024) NOT NULL
);

CREATE INDEX IF NOT EXISTS passages_corpus_document_idx ON passages (corpus_document_id);
