ALTER TABLE users
    ADD COLUMN IF NOT EXISTS google_sub text UNIQUE,
    ADD COLUMN IF NOT EXISTS email text;
