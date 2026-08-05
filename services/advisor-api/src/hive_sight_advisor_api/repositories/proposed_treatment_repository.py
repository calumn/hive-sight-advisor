from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import psycopg


@dataclass(frozen=True)
class ProposedTreatment:
    id: UUID
    hive_id: str
    jurisdiction_id: UUID
    answer_id: UUID
    status: str
    completed_at: datetime | None


class ProposedTreatmentRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def save(self, hive_id: str, jurisdiction_id: UUID, answer_id: UUID) -> ProposedTreatment:
        proposed_treatment_id = uuid4()
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO proposed_treatments (id, hive_id, jurisdiction_id, answer_id, status)
                VALUES (%s, %s, %s, %s, 'suggested')
                """,
                (proposed_treatment_id, hive_id, jurisdiction_id, answer_id),
            )
        self._connection.commit()
        return ProposedTreatment(
            id=proposed_treatment_id,
            hive_id=hive_id,
            jurisdiction_id=jurisdiction_id,
            answer_id=answer_id,
            status="suggested",
            completed_at=None,
        )

    def mark_completed(self, proposed_treatment_id: UUID) -> ProposedTreatment | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE proposed_treatments
                SET status = 'completed', completed_at = now()
                WHERE id = %s
                RETURNING id, hive_id, jurisdiction_id, answer_id, status, completed_at
                """,
                (proposed_treatment_id,),
            )
            row = cursor.fetchone()
        self._connection.commit()
        if row is None:
            return None
        return ProposedTreatment(
            id=row[0],
            hive_id=row[1],
            jurisdiction_id=row[2],
            answer_id=row[3],
            status=row[4],
            completed_at=row[5],
        )

    def find_by_id(self, proposed_treatment_id: UUID) -> ProposedTreatment | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, hive_id, jurisdiction_id, answer_id, status, completed_at
                FROM proposed_treatments
                WHERE id = %s
                """,
                (proposed_treatment_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return ProposedTreatment(
            id=row[0],
            hive_id=row[1],
            jurisdiction_id=row[2],
            answer_id=row[3],
            status=row[4],
            completed_at=row[5],
        )

    def find_latest_suggested_by_hive(self, hive_id: str) -> ProposedTreatment | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, hive_id, jurisdiction_id, answer_id, status, completed_at
                FROM proposed_treatments
                WHERE hive_id = %s AND status = 'suggested'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (hive_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return ProposedTreatment(
            id=row[0],
            hive_id=row[1],
            jurisdiction_id=row[2],
            answer_id=row[3],
            status=row[4],
            completed_at=row[5],
        )
