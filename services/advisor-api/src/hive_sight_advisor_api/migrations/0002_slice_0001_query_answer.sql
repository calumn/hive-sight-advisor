CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY,
    display_name text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspaces (
    id uuid PRIMARY KEY,
    display_name text,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspace_memberships (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id),
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    role text NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, workspace_id, role)
);

CREATE TABLE IF NOT EXISTS queries (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    text text NOT NULL,
    resolved_jurisdiction_id uuid REFERENCES jurisdictions(id),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS answers (
    id uuid PRIMARY KEY,
    query_id uuid NOT NULL REFERENCES queries(id),
    text text NOT NULL,
    grounding_status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS citations (
    id uuid PRIMARY KEY,
    answer_id uuid NOT NULL REFERENCES answers(id),
    passage_id uuid NOT NULL REFERENCES passages(id)
);
