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


def _build_workflow(
    postgres_connection,
    checkpointer,
    treatment_suggestion_provider=None,
    grounded_distance_threshold=0.5,
    partial_distance_threshold=0.8,
):
    answer_query_workflow = AnswerQueryWorkflow(
        corpus_repository=CorpusRepository(postgres_connection),
        embedding_provider=StubEmbeddingProvider(),
        generation_provider=StubGenerationProvider(),
        query_repository=PostgresQueryRepository(postgres_connection),
        grounded_distance_threshold=grounded_distance_threshold,
        partial_distance_threshold=partial_distance_threshold,
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


def test_reject_treatment_produces_a_revised_answer_superseding_the_rejected_one(
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
    workflow.request_treatment_plan(
        hive_id="hivesight-hive-10",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high, what treatment should I use?",
    )
    original = proposed_treatment_repository.find_latest_suggested_by_hive("hivesight-hive-10")
    assert original is not None

    outcome = workflow.reject_treatment(
        "hivesight-hive-10", reason="Conflicts with an active honey flow."
    )

    assert outcome is not None
    assert outcome.revision_exhausted is False
    assert outcome.answer.grounding_status == "grounded"
    assert len(suggestion_provider.suggestions) == 2  # original + revision

    original_after_rejection = proposed_treatment_repository.find_by_id(original.id)
    assert original_after_rejection is not None
    assert original_after_rejection.status == "rejected"

    revised = proposed_treatment_repository.find_latest_suggested_by_hive("hivesight-hive-10")
    assert revised is not None
    assert revised.id != original.id
    assert revised.supersedes_proposed_treatment_id == original.id


def test_reject_treatment_returns_none_when_nothing_is_suggested(
    postgres_connection, checkpointer
) -> None:
    workflow, _ = _build_workflow(postgres_connection, checkpointer)

    outcome = workflow.reject_treatment("hivesight-hive-does-not-exist", reason="No reason")

    assert outcome is None


def test_reject_treatment_exhausts_after_max_revisions_and_preserves_the_last_suggestion(
    postgres_connection, checkpointer
) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    workflow, proposed_treatment_repository = _build_workflow(postgres_connection, checkpointer)
    workflow.request_treatment_plan(
        hive_id="hivesight-hive-11",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high, what treatment should I use?",
    )

    # 3 revisions (1 original + 3 = 4 suggestions total) should each succeed normally.
    for i in range(3):
        outcome = workflow.reject_treatment("hivesight-hive-11", reason=f"Reason {i}")
        assert outcome is not None
        assert outcome.revision_exhausted is False

    last_suggested_before_exhaustion = proposed_treatment_repository.find_latest_suggested_by_hive(
        "hivesight-hive-11"
    )
    assert last_suggested_before_exhaustion is not None

    # The 4th rejection should be flagged exhausted, produce no new Proposed Treatment...
    exhausted_outcome = workflow.reject_treatment("hivesight-hive-11", reason="Reason 3")

    assert exhausted_outcome is not None
    assert exhausted_outcome.revision_exhausted is True

    still_last_suggested = proposed_treatment_repository.find_latest_suggested_by_hive(
        "hivesight-hive-11"
    )
    assert still_last_suggested is not None
    assert still_last_suggested.id == last_suggested_before_exhaustion.id

    # ...and the last suggestion must still be genuinely acceptable — proving the
    # exhausted rejection never actually resumed (and thereby consumed) the graph's
    # suspended state.
    completed = workflow.confirm_completed("hivesight-hive-11")
    assert completed is not None
    assert completed.id == last_suggested_before_exhaustion.id
    assert completed.status == "completed"


def _seed_jurisdiction_with_realistically_embedded_passage(cursor, jurisdiction_id) -> str:
    # Unlike _seed_jurisdiction_with_passage's all-zero placeholder (which pgvector's
    # cosine distance treats as trivially "close" to everything, useful for the
    # always-grounded tests above but useless for a genuine ungrounded case), this
    # embeds the passage text for real via the stub provider so retrieval distance
    # reflects actual word overlap.
    passage_text = "Treat varroa with oxalic acid vaporisation."
    corpus_document_id = uuid.uuid4()
    passage_id = uuid.uuid4()
    embedding = StubEmbeddingProvider().embed(passage_text)
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
        (passage_id, corpus_document_id, passage_text, embedding),
    )
    return passage_text


def test_reject_treatment_when_the_revision_itself_is_ungrounded(
    postgres_connection, checkpointer
) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_realistically_embedded_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    workflow, proposed_treatment_repository = _build_workflow(
        postgres_connection,
        checkpointer,
        grounded_distance_threshold=0.35,
        partial_distance_threshold=0.55,
    )
    workflow.request_treatment_plan(
        hive_id="hivesight-hive-12",
        jurisdiction_id=jurisdiction_id,
        query_text="How do I treat varroa with oxalic acid vaporisation?",
    )
    original = proposed_treatment_repository.find_latest_suggested_by_hive("hivesight-hive-12")
    assert original is not None

    outcome = workflow.reject_treatment(
        "hivesight-hive-12",
        reason=(
            "giraffe astronomy bicycle continent orchestra volcano telephone galaxy "
            "umbrella xylophone quokka marmalade lighthouse saxophone tundra"
        ),
    )

    assert outcome is not None
    assert outcome.answer.grounding_status == "ungrounded"
    assert outcome.revision_exhausted is False
    assert proposed_treatment_repository.find_latest_suggested_by_hive("hivesight-hive-12") is None


def test_repeating_a_request_while_a_suggestion_is_still_pending_returns_the_same_suggestion(
    postgres_connection, checkpointer
) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    workflow, proposed_treatment_repository = _build_workflow(postgres_connection, checkpointer)
    first = workflow.request_treatment_plan(
        hive_id="hivesight-hive-20",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high, what treatment should I use?",
    )
    first_proposed = proposed_treatment_repository.find_latest_suggested_by_hive("hivesight-hive-20")
    assert first_proposed is not None

    second = workflow.request_treatment_plan(
        hive_id="hivesight-hive-20",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high, what treatment should I use?",
    )

    assert second.id == first.id

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM proposed_treatments WHERE hive_id = %s", ("hivesight-hive-20",)
        )
        (count,) = cursor.fetchone()
    assert count == 1


def test_requesting_again_after_a_suggestion_was_completed_starts_a_fresh_episode(
    postgres_connection, checkpointer
) -> None:
    jurisdiction_id = uuid.uuid4()
    with postgres_connection.cursor() as cursor:
        _seed_jurisdiction_with_passage(cursor, jurisdiction_id)
    postgres_connection.commit()

    workflow, _proposed_treatment_repository = _build_workflow(postgres_connection, checkpointer)
    first = workflow.request_treatment_plan(
        hive_id="hivesight-hive-21",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high, what treatment should I use?",
    )
    workflow.confirm_completed("hivesight-hive-21")

    second = workflow.request_treatment_plan(
        hive_id="hivesight-hive-21",
        jurisdiction_id=jurisdiction_id,
        query_text="Mite count is high again, what treatment should I use this time?",
    )

    assert second.id != first.id

    with postgres_connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM proposed_treatments WHERE hive_id = %s", ("hivesight-hive-21",)
        )
        (count,) = cursor.fetchone()
    assert count == 2
