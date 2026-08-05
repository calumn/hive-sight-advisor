-- A dedicated internal Workspace for Query/Answer records produced by agentic,
-- app-to-app requests (Slice 0008) that have no real Beekeeper/Workspace context —
-- not a real Beekeeper's Workspace. See requirements/decision-log.md,
-- "Agentic Treatment Plan Request Mechanism".
INSERT INTO workspaces (id, display_name, status)
VALUES ('00000000-0000-0000-0000-000000000001', 'HiveSight Integration (System)', 'active')
ON CONFLICT (id) DO NOTHING;
