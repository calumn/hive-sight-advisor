class StubTreatmentSuggestionProvider:
    """Stands in for HiveSight's not-yet-built accept-suggestion endpoint.

    HiveSight has no real endpoint to call yet (see the
    hivesight-advisor-integration-contract skill for current status), so this
    records what would have been sent rather than making a network call.
    """

    def __init__(self) -> None:
        self.suggestions: list[tuple[str, str]] = []

    def suggest_treatment(self, hive_id: str, answer_text: str) -> None:
        self.suggestions.append((hive_id, answer_text))
