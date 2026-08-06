ALTER TABLE proposed_treatments
    ADD COLUMN IF NOT EXISTS supersedes_proposed_treatment_id uuid REFERENCES proposed_treatments(id);
