from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import psycopg


@dataclass(frozen=True)
class ProvisionedIdentity:
    user_id: UUID
    workspace_id: UUID


class UserProvisioningRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def find_or_provision(
        self, google_sub: str, email: str | None, display_name: str | None
    ) -> ProvisionedIdentity:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE google_sub = %s", (google_sub,))
            row = cursor.fetchone()
            if row is not None:
                user_id = row[0]
                cursor.execute(
                    """
                    SELECT workspace_id FROM workspace_memberships
                    WHERE user_id = %s AND role = 'owner'
                    """,
                    (user_id,),
                )
                workspace_id = cursor.fetchone()[0]
            else:
                user_id = uuid4()
                workspace_id = uuid4()
                cursor.execute(
                    "INSERT INTO users (id, google_sub, email, display_name) VALUES (%s, %s, %s, %s)",
                    (user_id, google_sub, email, display_name),
                )
                cursor.execute(
                    "INSERT INTO workspaces (id, display_name) VALUES (%s, %s)",
                    (workspace_id, display_name),
                )
                cursor.execute(
                    """
                    INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
                    VALUES (%s, %s, %s, 'owner', 'active')
                    """,
                    (uuid4(), user_id, workspace_id),
                )
        self._connection.commit()
        return ProvisionedIdentity(user_id=user_id, workspace_id=workspace_id)
