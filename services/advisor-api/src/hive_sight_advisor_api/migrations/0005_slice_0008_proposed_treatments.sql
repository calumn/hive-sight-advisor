CREATE TABLE IF NOT EXISTS proposed_treatments (
    id uuid PRIMARY KEY,
    hive_id text NOT NULL,
    jurisdiction_id uuid NOT NULL REFERENCES jurisdictions(id),
    answer_id uuid NOT NULL REFERENCES answers(id),
    status text NOT NULL DEFAULT 'suggested',
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE INDEX IF NOT EXISTS proposed_treatments_hive_id_idx ON proposed_treatments (hive_id);
