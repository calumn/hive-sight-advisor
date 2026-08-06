from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import psycopg

_COLUMNS = (
    "id, hive_id, jurisdiction_id, answer_id, status, completed_at, "
    "supersedes_proposed_treatment_id"
)


@dataclass(frozen=True)
class ProposedTreatment:
    id: UUID
    hive_id: str
    jurisdiction_id: UUID
    answer_id: UUID
    status: str
    completed_at: datetime | None
    supersedes_proposed_treatment_id: UUID | None = None


def _from_row(row: tuple) -> ProposedTreatment:
    return ProposedTreatment(
        id=row[0],
        hive_id=row[1],
        jurisdiction_id=row[2],
        answer_id=row[3],
        status=row[4],
        completed_at=row[5],
        supersedes_proposed_treatment_id=row[6],
    )


class ProposedTreatmentRepository:
    def __init__(self, connection: psycopg.Connection) -> None:
        self._connection = connection

    def save(
        self,
        hive_id: str,
        jurisdiction_id: UUID,
        answer_id: UUID,
        supersedes_proposed_treatment_id: UUID | None = None,
    ) -> ProposedTreatment:
        proposed_treatment_id = uuid4()
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO proposed_treatments
                    (id, hive_id, jurisdiction_id, answer_id, status, supersedes_proposed_treatment_id)
                VALUES (%s, %s, %s, %s, 'suggested', %s)
                """,
                (
                    proposed_treatment_id,
                    hive_id,
                    jurisdiction_id,
                    answer_id,
                    supersedes_proposed_treatment_id,
                ),
            )
        self._connection.commit()
        return ProposedTreatment(
            id=proposed_treatment_id,
            hive_id=hive_id,
            jurisdiction_id=jurisdiction_id,
            answer_id=answer_id,
            status="suggested",
            completed_at=None,
            supersedes_proposed_treatment_id=supersedes_proposed_treatment_id,
        )

    def mark_completed(self, proposed_treatment_id: UUID) -> ProposedTreatment | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE proposed_treatments
                SET status = 'completed', completed_at = now()
                WHERE id = %s
                RETURNING {_COLUMNS}
                """,
                (proposed_treatment_id,),
            )
            row = cursor.fetchone()
        self._connection.commit()
        return _from_row(row) if row is not None else None

    def mark_rejected(self, proposed_treatment_id: UUID) -> ProposedTreatment | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE proposed_treatments
                SET status = 'rejected'
                WHERE id = %s
                RETURNING {_COLUMNS}
                """,
                (proposed_treatment_id,),
            )
            row = cursor.fetchone()
        self._connection.commit()
        return _from_row(row) if row is not None else None

    def find_by_id(self, proposed_treatment_id: UUID) -> ProposedTreatment | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {_COLUMNS} FROM proposed_treatments WHERE id = %s",
                (proposed_treatment_id,),
            )
            row = cursor.fetchone()
        return _from_row(row) if row is not None else None

    def find_latest_suggested_by_hive(self, hive_id: str) -> ProposedTreatment | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {_COLUMNS}
                FROM proposed_treatments
                WHERE hive_id = %s AND status = 'suggested'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (hive_id,),
            )
            row = cursor.fetchone()
        return _from_row(row) if row is not None else None
