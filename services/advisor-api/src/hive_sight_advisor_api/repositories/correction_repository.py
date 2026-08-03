from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import psycopg


@dataclass(frozen=True)
class Correction:
    id: UUID
    workspace_id: UUID
    answer_id: UUID
    created_by_user_id: UUID
    notes: str
    status: str


class CorrectionRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def answer_belongs_to_workspace(self, answer_id: UUID, workspace_id: UUID) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM answers
                JOIN queries ON queries.id = answers.query_id
                WHERE answers.id = %s AND queries.workspace_id = %s
                """,
                (answer_id, workspace_id),
            )
            return cursor.fetchone() is not None

    def save(
        self,
        workspace_id: UUID,
        answer_id: UUID,
        created_by_user_id: UUID,
        notes: str,
    ) -> Correction:
        correction_id = uuid4()
        status = "trusted"
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO corrections
                    (id, workspace_id, answer_id, created_by_user_id, notes, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (correction_id, workspace_id, answer_id, created_by_user_id, notes, status),
            )
        self._connection.commit()
        return Correction(
            id=correction_id,
            workspace_id=workspace_id,
            answer_id=answer_id,
            created_by_user_id=created_by_user_id,
            notes=notes,
            status=status,
        )
