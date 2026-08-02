from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "advisor-api" / "src"))

import psycopg
from pgvector.psycopg import register_vector

from hive_sight_advisor_api.adapters.embedding_voyage import VoyageEmbeddingProvider
from hive_sight_advisor_api.db import apply_migrations
from hive_sight_advisor_api.settings import load_settings

DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000101")
DEV_WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000000201")
DEV_MEMBERSHIP_ID = UUID("00000000-0000-0000-0000-000000000301")
UK_JURISDICTION_ID = UUID("00000000-0000-0000-0000-000000000401")
VARROA_GUIDE_DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000501")
VARROA_GUIDE_PASSAGE_ID = UUID("00000000-0000-0000-0000-000000000601")

PASSAGE_TEXT = (
    "Varroa destructor mites are treated using an integrated pest management approach. "
    "In the UK, the most common autumn treatment is oxalic acid vaporisation, applied when "
    "the colony is broodless in late autumn or early winter, since oxalic acid only kills "
    "phoretic mites riding on adult bees and has no effect on mites sealed inside brood cells. "
    "Monitor mite drop with a sticky board for at least a week before and after treatment to "
    "confirm efficacy, and always follow the product label for dose and safety precautions."
)


def seed(database_url: str, voyage_api_key: str) -> None:
    apply_migrations(database_url)
    embedding = VoyageEmbeddingProvider(api_key=voyage_api_key).embed(PASSAGE_TEXT)

    with psycopg.connect(database_url) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING",
                (DEV_USER_ID,),
            )
            cursor.execute(
                """
                INSERT INTO workspaces (id, display_name) VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (DEV_WORKSPACE_ID, "Dev Workspace"),
            )
            cursor.execute(
                """
                INSERT INTO workspace_memberships (id, user_id, workspace_id, role, status)
                VALUES (%s, %s, %s, 'owner', 'active')
                ON CONFLICT (user_id, workspace_id, role) DO NOTHING
                """,
                (DEV_MEMBERSHIP_ID, DEV_USER_ID, DEV_WORKSPACE_ID),
            )
            cursor.execute(
                """
                INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (UK_JURISDICTION_ID, "uk", "United Kingdom"),
            )
            cursor.execute(
                """
                INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    VARROA_GUIDE_DOCUMENT_ID,
                    UK_JURISDICTION_ID,
                    "Managing Varroa: A Guide for UK Beekeepers",
                    "Healthy Bees Healthy Colonies (HBHC) guide",
                    "CC BY-NC-ND",
                ),
            )
            cursor.execute(
                """
                INSERT INTO passages (id, corpus_document_id, text_content, embedding)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (VARROA_GUIDE_PASSAGE_ID, VARROA_GUIDE_DOCUMENT_ID, PASSAGE_TEXT, embedding),
            )
        connection.commit()

    print("Seeded Slice 0001 dev data:")
    print(f"  dev user id:        {DEV_USER_ID}")
    print(f"  dev workspace id:   {DEV_WORKSPACE_ID}")
    print(f"  UK jurisdiction id: {UK_JURISDICTION_ID}")


def main() -> None:
    settings = load_settings()
    if not settings.voyage_api_key:
        raise SystemExit("Set VOYAGE_API_KEY before running the seed script.")
    seed(settings.database_url, settings.voyage_api_key)


if __name__ == "__main__":
    main()
