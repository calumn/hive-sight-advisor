import uuid

from langgraph.checkpoint.postgres import PostgresSaver

from hive_sight_advisor_api.adapters.embedding_stub import StubEmbeddingProvider
from hive_sight_advisor_api.adapters.generation_stub import StubGenerationProvider
from hive_sight_advisor_api.adapters.treatment_suggestion_stub import (
    StubTreatmentSuggestionProvider,
)
from hive_sight_advisor_api.db import test_database_url as get_test_database_url
from hive_sight_advisor_api.repositories.corpus_repository import CorpusRepository
from hive_sight_advisor_api.repositories.proposed_treatment_repository import (
    ProposedTreatmentRepository,
)
from hive_sight_advisor_api.repositories.query_repository import PostgresQueryRepository
from hive_sight_advisor_api.settings import load_settings
from hive_sight_advisor_api.workflows.answer_query import AnswerQueryWorkflow
from hive_sight_advisor_api.workflows.treatment_plan_workflow import TreatmentPlanWorkflow


def _seed_jurisdiction_with_passage(cursor, jurisdiction_id) -> None:
    corpus_document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    embedding = [0.0] * 1024
    cursor.execute(
        "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
        (jurisdiction_id, "uk", "United Kingdom"),
    )
    cursor.execute(
        """
        INSERT INTO corpus_documents (id, jurisdiction_id, title, source, source_url, licence_terms)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            corpus_document_id,
            jurisdiction_id,
            "Varroa Guide",
            "APHA BeeBase",
            "https://www.nationalbeeunit.com/",
            "Open Government Licence",
        ),
    )
    cursor.execute(
        """
        INSERT INTO passages (id, corpus_document_id, text_content, embedding)
        VALUES (%s, %s, %s, %s)
        """,
        (passage_id, corpus_document_id, "Treat varroa with oxalic acid vaporisation.", embedding),
    )


def _build_workflow(postgres_connection, checkpointer, treatment_suggestion_provider=None):
    answer_query_workflow = AnswerQueryWorkflow(
        corpus_repository=CorpusRepository(postgres_connection),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=StubGenerationProvider(),
        query_repository=PostgresQueryRepository(postgres_connection),
        grounded_distance_threshold=0.5,
        partial_distance_threshold=0.8,
    )
    proposed_treatment_repository = ProposedTreatmentRepository(postgres_connection)
    return TreatmentPlanWorkflow(
        answer_query_workflow=answer_query_workflow,
        treatment_suggestion_provider=treatment_suggestion_provider or StubTreatmentSuggestionProvider(),
        proposed_treatment_repository=proposed_treatment_repository,
        checkpointer=checkpointer,
    ), proposed_treatment_repository


def test_grounded_request_records_a_suggested_proposed_treatment(
    postgres_connection, checkpointer
) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    suggestion_provider = StubTreatmentSuggestionProvider()
    workflow, proposed_treatment_repository = _build_workflow(
        postgres_connection, checkpointer, suggestion_provider
    )

    answer = workflow.request_treatment_plan(
        hive_id="hivesight-hive-42",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high, what treatment should I use?",
    )

    assert answer.grounding_status == "grounded"
    assert suggestion_provider.suggestions  # the stub "suggest" call was made
    proposed_treatment = proposed_treatment_repository.find_latest_suggested_by_hive(
        "hivesight-hive-42"
    )
    assert proposed_treatment is not None
    assert proposed_treatment.status == "suggested"


def test_ungrounded_request_records_no_proposed_treatment(postgres_connection, checkpointer) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO jurisdictions (id, code, display_name) VALUES (%s, %s, %s)",
            (jurisdiction_id, "uk", "United Kingdom"),
        )
    postgres_connection.commit()

    suggestion_provider = StubTreatmentSuggestionProvider()
    workflow, proposed_treatment_repository = _build_workflow(
        postgres_connection, checkpointer, suggestion_provider
    )

    answer = workflow.request_treatment_plan(
        hive_id="hivesight-hive-99",
        jurisdiction_id=jurisdiction_id,
        query_text="Should I paint my hive a different colour?",
    )

    assert answer.grounding_status == "ungrounded"
    assert suggestion_provider.suggestions == []
    assert proposed_treatment_repository.find_latest_suggested_by_hive("hivesight-hive-99") is None


def test_confirm_completed_resumes_and_marks_the_treatment_completed(
    postgres_connection, checkpointer
) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    workflow, proposed_treatment_repository = _build_workflow(postgres_connection, checkpointer)
    workflow.request_treatment_plan(
        hive_id="hivesight-hive-7",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high, what treatment should I use?",
    )
    proposed_treatment = proposed_treatment_repository.find_latest_suggested_by_hive(
        "hivesight-hive-7"
    )
    assert proposed_treatment is not None

    # Resume via a *different* checkpointer connection and a freshly compiled graph
    # object, standing in for a process restart — proving the suspend survived in
    # Postgres itself, not merely in the first workflow's in-memory graph object.
    database_url = get_test_database_url(load_settings().database_url)
    with PostgresSaver.from_conn_string(database_url) as fresh_checkpointer:
        fresh_workflow, _ = _build_workflow(postgres_connection, fresh_checkpointer)
        completed = fresh_workflow.confirm_completed("hivesight-hive-7")

    assert completed is not None
    assert completed.status == "completed"
    assert completed.completed_at is not None
