from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

import psycopg
from pgvector.psycopg import register_vector

from hive_sight_advisor_api.adapters.embedding_provider import EmbeddingProvider
from hive_sight_advisor_api.adapters.embedding_voyage import VoyageEmbeddingProvider
from hive_sight_advisor_api.db import apply_migrations
from hive_sight_advisor_api.settings import load_settings

DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000101")
DEV_WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000000201")
DEV_MEMBERSHIP_ID = UUID("00000000-0000-0000-0000-000000000301")

UK_JURISDICTION_ID = UUID("00000000-0000-0000-0000-000000000401")
US_JURISDICTION_ID = UUID("00000000-0000-0000-0000-000000000402")

UK_GUIDE_DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000501")
UK_GUIDE_PASSAGE_ID = UUID("00000000-0000-0000-0000-000000000601")
US_GUIDE_DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000502")
US_GUIDE_PASSAGE_ID = UUID("00000000-0000-0000-0000-000000000602")

UK_PASSAGE_TEXT = (
    "Varroa destructor mites are treated using an integrated pest management approach. "
    "In the UK, the most common autumn treatment is oxalic acid vaporisation, applied when "
    "the colony is broodless in late autumn or early winter, since oxalic acid only kills "
    "phoretic mites riding on adult bees and has no effect on mites sealed inside brood cells. "
    "Monitor mite drop with a sticky board for at least a week before and after treatment to "
    "confirm efficacy, and always follow the product label for dose and safety precautions."
)

US_PASSAGE_TEXT = (
    "The Honey Bee Health Coalition's integrated pest management approach for Varroa starts "
    "with monitoring, not treatment: use an alcohol wash or sugar roll to measure mite load as "
    "mites per 100 bees, and treat once the count exceeds an economic threshold of about 2 to 3 "
    "mites per 100 bees, rather than treating on a fixed calendar schedule. Once treatment is "
    "warranted, rotate between different registered active ingredients across the season - for "
    "example amitraz-based strips, formic acid pads, or oxalic acid - rather than using the same "
    "product repeatedly, since repeated use of one active ingredient accelerates resistance "
    "development in the mite population. Always follow the product label for application "
    "timing, temperature range, and honey super restrictions specific to each active ingredient."
)


@dataclass(frozen=True)
class SeedJurisdiction:
    jurisdiction_id: UUID
    code: str
    display_name: str
    document_id: UUID
    document_title: str
    document_source: str
    licence_terms: str
    passage_id: UUID
    passage_text: str


JURISDICTIONS = [
    SeedJurisdiction(
        jurisdiction_id=UK_JURISDICTION_ID,
        code="uk",
        display_name="United Kingdom",
        document_id=UK_GUIDE_DOCUMENT_ID,
        document_title="Managing Varroa: A Guide for UK Beekeepers",
        document_source="APHA BeeBase",
        licence_terms="Open Government Licence",
        passage_id=UK_GUIDE_PASSAGE_ID,
        passage_text=UK_PASSAGE_TEXT,
    ),
    SeedJurisdiction(
        jurisdiction_id=US_JURISDICTION_ID,
        code="us",
        display_name="United States",
        document_id=US_GUIDE_DOCUMENT_ID,
        document_title="Tools for Varroa Management",
        document_source="Honey Bee Health Coalition (HBHC)",
        licence_terms="CC BY-NC-ND",
        passage_id=US_GUIDE_PASSAGE_ID,
        passage_text=US_PASSAGE_TEXT,
    ),
]


def seed(database_url: str, embedding_provider: EmbeddingProvider) -> None:
    apply_migrations(database_url)

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

            for jurisdiction in JURISDICTIONS:
                cursor.execute(
                    """
                    INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (jurisdiction.jurisdiction_id, jurisdiction.code, jurisdiction.display_name),
                )
                cursor.execute(
                    """
                    INSERT INTO corpus_documents (id, jurisdiction_id, title, source, licence_terms)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        licence_terms = EXCLUDED.licence_terms
                    """,
                    (
                        jurisdiction.document_id,
                        jurisdiction.jurisdiction_id,
                        jurisdiction.document_title,
                        jurisdiction.document_source,
                        jurisdiction.licence_terms,
                    ),
                )
                embedding = embedding_provider.embed(jurisdiction.passage_text)
                cursor.execute(
                    """
                    INSERT INTO passages (id, corpus_document_id, text_content, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text_content = EXCLUDED.text_content,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        jurisdiction.passage_id,
                        jurisdiction.document_id,
                        jurisdiction.passage_text,
                        embedding,
                    ),
                )
        connection.commit()

    print("Seeded Slice 0001/0002 dev data:")
    print(f"  dev user id:      {DEV_USER_ID}")
    print(f"  dev workspace id: {DEV_WORKSPACE_ID}")
    for jurisdiction in JURISDICTIONS:
        print(f"  {jurisdiction.display_name} jurisdiction id: {jurisdiction.jurisdiction_id}")


def main() -> None:
    settings = load_settings()
    if not settings.voyage_api_key:
        raise SystemExit("Set VOYAGE_API_KEY before running the seed script.")
    seed(settings.database_url, VoyageEmbeddingProvider(api_key=settings.voyage_api_key))


if __name__ == "__main__":
    main()
