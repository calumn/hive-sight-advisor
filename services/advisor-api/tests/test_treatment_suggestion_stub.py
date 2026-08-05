from hive_sight_advisor_api.adapters.treatment_suggestion_stub import (
    StubTreatmentSuggestionProvider,
)


def test_stub_records_a_suggestion() -> None:
    provider = StubTreatmentSuggestionProvider()

    provider.suggest_treatment(hive_id="hivesight-hive-42", answer_text="Apply oxalic acid.")

    assert provider.suggestions == [("hivesight-hive-42", "Apply oxalic acid.")]
