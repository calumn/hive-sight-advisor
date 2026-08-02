from __future__ import annotations

from uuid import UUID

import psycopg

from hive_sight_advisor_api.workflows.answer_query import Answer


class PostgresQueryRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def has_active_membership(self, user_id: UUID, workspace_id: UUID) -> bool:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM workspace_memberships
                WHERE user_id = %s AND workspace_id = %s AND status = 'active'
                """,
                (user_id, workspace_id),
            )
            return cursor.fetchone() is not None

    def save(
        self,
        workspace_id: UUID,
        query_id: UUID,
        query_text: str,
        jurisdiction_id: UUID,
        answer: Answer,
    ) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO queries (id, workspace_id, text, resolved_jurisdiction_id)
                VALUES (%s, %s, %s, %s)
                """,
                (query_id, workspace_id, query_text, jurisdiction_id),
            )
            cursor.execute(
                """
                INSERT INTO answers (id, query_id, text, grounding_status)
                VALUES (%s, %s, %s, %s)
                """,
                (answer.id, query_id, answer.text, answer.grounding_status),
            )
            for citation in answer.citations:
                cursor.execute(
                    "INSERT INTO citations (id, answer_id, passage_id) VALUES (%s, %s, %s)",
                    (citation.id, answer.id, citation.passage_id),
                )
        self._connection.commit()
