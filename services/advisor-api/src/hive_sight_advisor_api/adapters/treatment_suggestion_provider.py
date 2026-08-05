from typing import Protocol


class TreatmentSuggestionProvider(Protocol):
    def suggest_treatment(self, hive_id: str, answer_text: str) -> None: ...
