CREATE TABLE IF NOT EXISTS corrections (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    answer_id uuid NOT NULL REFERENCES answers(id),
    created_by_user_id uuid NOT NULL REFERENCES users(id),
    notes text NOT NULL,
    status text NOT NULL DEFAULT 'trusted',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS corrections_answer_id_idx ON corrections (answer_id);
