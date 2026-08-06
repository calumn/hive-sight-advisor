from __future__ import annotations

from uuid import UUID

import psycopg


class JurisdictionRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def find_id_by_code(self, code: str) -> UUID | None:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id FROM jurisdictions WHERE code = %s", (code,))
            row = cursor.fetchone()
        return row[0] if row is not None else None
