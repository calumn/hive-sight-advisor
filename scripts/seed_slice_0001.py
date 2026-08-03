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

UK_OLD_GUIDE_DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000503")
UK_OLD_GUIDE_PASSAGE_ID = UUID("00000000-0000-0000-0000-000000000603")

UK_APIVAR_DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000504")
UK_APIVAR_PASSAGE_ID = UUID("00000000-0000-0000-0000-000000000604")
UK_APIGUARD_DOCUMENT_ID = UUID("00000000-0000-0000-0000-000000000505")
UK_APIGUARD_PASSAGE_ID = UUID("00000000-0000-0000-0000-000000000605")

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

UK_OLD_PASSAGE_TEXT = (
    "Older APHA guidance (since updated) recommended Apistan (fluvalinate) strips as the "
    "primary autumn Varroa treatment, left in the hive for six to eight weeks during a "
    "broodless period. This guidance has been superseded due to widespread fluvalinate "
    "resistance in UK Varroa populations; consult current guidance for up-to-date treatment "
    "recommendations."
)

UK_APIVAR_PASSAGE_TEXT = (
    "Apivar is a UK-authorised Varroa treatment using amitraz-impregnated strips hung between "
    "the brood frames. Unlike temperature-sensitive treatments, Apivar has no temperature "
    "restriction and can be used at any time of year. Strips are left in place for six to ten "
    "weeks depending on brood size and season, with the longer duration recommended in autumn. "
    "Honey supers must be removed before treatment, since amitraz is not permitted while supers "
    "intended for human consumption are on the hive. Amitraz is a synthetic acaricide and is not "
    "compatible with organic certification standards."
)

UK_APIGUARD_PASSAGE_TEXT = (
    "Apiguard is a UK-authorised Varroa treatment based on thymol, a compound derived from thyme "
    "oil, supplied as a gel tray placed on top of the brood frames. It works best when daytime "
    "temperatures reach at least fifteen degrees Celsius, making it a warmer-months treatment "
    "rather than a year-round option. The standard regime is two fifty-gram doses roughly two "
    "weeks apart, for a total treatment period of around four to six weeks. As with other "
    "chemical treatments, honey supers must be removed before treatment and only replaced once "
    "treatment is complete. Because thymol is plant-derived, Apiguard is compatible with organic "
    "certification standards, unlike synthetic acaricides such as amitraz."
)


@dataclass(frozen=True)
class SeedJurisdiction:
    jurisdiction_id: UUID
    code: str
    display_name: str
    document_id: UUID
    document_title: str
    document_source: str
    source_url: str
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
        source_url="https://www.nationalbeeunit.com/",
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
        source_url="https://honeybeehealthcoalition.org/varroa/",
        licence_terms="CC BY-NC-ND",
        passage_id=US_GUIDE_PASSAGE_ID,
        passage_text=US_PASSAGE_TEXT,
    ),
]


@dataclass(frozen=True)
class SupersededDocument:
    jurisdiction_id: UUID
    document_id: UUID
    document_title: str
    document_source: str
    source_url: str
    licence_terms: str
    superseded_by_document_id: UUID
    passage_id: UUID
    passage_text: str


SUPERSEDED_DOCUMENTS = [
    SupersededDocument(
        jurisdiction_id=UK_JURISDICTION_ID,
        document_id=UK_OLD_GUIDE_DOCUMENT_ID,
        document_title="Managing Varroa: A Guide for UK Beekeepers (2015 edition)",
        document_source="APHA BeeBase",
        source_url="https://www.nationalbeeunit.com/",
        licence_terms="Open Government Licence",
        superseded_by_document_id=UK_GUIDE_DOCUMENT_ID,
        passage_id=UK_OLD_GUIDE_PASSAGE_ID,
        passage_text=UK_OLD_PASSAGE_TEXT,
    ),
]


@dataclass(frozen=True)
class AdditionalDocument:
    jurisdiction_id: UUID
    document_id: UUID
    document_title: str
    document_source: str
    source_url: str
    licence_terms: str
    passage_id: UUID
    passage_text: str


# Additional real UK treatment-option documents, alongside the primary jurisdiction guide, so
# there is more than one genuine treatment option per jurisdiction to compare (prerequisite for
# FR-004). Unlike the primary guide's Open Government Licence source, these come from a retailer
# product page and a manufacturer FAQ respectively, so their licence terms are framed honestly as
# "all rights reserved" rather than borrowing the OGL framing of the primary document.
ADDITIONAL_DOCUMENTS = [
    AdditionalDocument(
        jurisdiction_id=UK_JURISDICTION_ID,
        document_id=UK_APIVAR_DOCUMENT_ID,
        document_title="Apivar (Amitraz) Varroa Treatment",
        document_source="Thorne (Beehives) Ltd — product information",
        source_url="https://www.thorne.co.uk/health-feeding/pests-diseases/varroa/varroa-chemical/apivar.html",
        licence_terms="All rights reserved (retailer product literature)",
        passage_id=UK_APIVAR_PASSAGE_ID,
        passage_text=UK_APIVAR_PASSAGE_TEXT,
    ),
    AdditionalDocument(
        jurisdiction_id=UK_JURISDICTION_ID,
        document_id=UK_APIGUARD_DOCUMENT_ID,
        document_title="Apiguard (Thymol) Varroa Treatment",
        document_source="Vita Bee Health — manufacturer FAQ",
        source_url="https://www.vita-europe.com/beehealth/wp-content/uploads/apiguard-faq.pdf",
        licence_terms="All rights reserved (manufacturer product literature)",
        passage_id=UK_APIGUARD_PASSAGE_ID,
        passage_text=UK_APIGUARD_PASSAGE_TEXT,
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
                    INSERT INTO corpus_documents (id, jurisdiction_id, title, source, source_url, licence_terms)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        source_url = EXCLUDED.source_url,
                        licence_terms = EXCLUDED.licence_terms
                    """,
                    (
                        jurisdiction.document_id,
                        jurisdiction.jurisdiction_id,
                        jurisdiction.document_title,
                        jurisdiction.document_source,
                        jurisdiction.source_url,
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

            for superseded in SUPERSEDED_DOCUMENTS:
                cursor.execute(
                    """
                    INSERT INTO corpus_documents
                        (id, jurisdiction_id, title, source, source_url, licence_terms, status,
                         superseded_by_corpus_document_id)
                    VALUES (%s, %s, %s, %s, %s, %s, 'superseded', %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        source_url = EXCLUDED.source_url,
                        licence_terms = EXCLUDED.licence_terms,
                        status = EXCLUDED.status,
                        superseded_by_corpus_document_id = EXCLUDED.superseded_by_corpus_document_id
                    """,
                    (
                        superseded.document_id,
                        superseded.jurisdiction_id,
                        superseded.document_title,
                        superseded.document_source,
                        superseded.source_url,
                        superseded.licence_terms,
                        superseded.superseded_by_document_id,
                    ),
                )
                embedding = embedding_provider.embed(superseded.passage_text)
                cursor.execute(
                    """
                    INSERT INTO passages (id, corpus_document_id, text_content, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text_content = EXCLUDED.text_content,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        superseded.passage_id,
                        superseded.document_id,
                        superseded.passage_text,
                        embedding,
                    ),
                )
            for additional in ADDITIONAL_DOCUMENTS:
                cursor.execute(
                    """
                    INSERT INTO corpus_documents (id, jurisdiction_id, title, source, source_url, licence_terms)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        source_url = EXCLUDED.source_url,
                        licence_terms = EXCLUDED.licence_terms
                    """,
                    (
                        additional.document_id,
                        additional.jurisdiction_id,
                        additional.document_title,
                        additional.document_source,
                        additional.source_url,
                        additional.licence_terms,
                    ),
                )
                embedding = embedding_provider.embed(additional.passage_text)
                cursor.execute(
                    """
                    INSERT INTO passages (id, corpus_document_id, text_content, embedding)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text_content = EXCLUDED.text_content,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        additional.passage_id,
                        additional.document_id,
                        additional.passage_text,
                        embedding,
                    ),
                )
        connection.commit()

    print("Seeded Slice 0001/0002 dev data:")
    print(f"  dev user id:      {DEV_USER_ID}")
    print(f"  dev workspace id: {DEV_WORKSPACE_ID}")
    for jurisdiction in JURISDICTIONS:
        print(f"  {jurisdiction.display_name} jurisdiction id: {jurisdiction.jurisdiction_id}")
    for superseded in SUPERSEDED_DOCUMENTS:
        print(f"  superseded document seeded: {superseded.document_title}")
    for additional in ADDITIONAL_DOCUMENTS:
        print(f"  additional treatment-option document seeded: {additional.document_title}")


def main() -> None:
    settings = load_settings()
    if not settings.voyage_api_key:
        raise SystemExit("Set VOYAGE_API_KEY before running the seed script.")
    seed(settings.database_url, VoyageEmbeddingProvider(api_key=settings.voyage_api_key))


if __name__ == "__main__":
    main()
