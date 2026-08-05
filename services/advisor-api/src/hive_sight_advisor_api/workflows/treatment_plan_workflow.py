from __future__ import annotations

from typing import Any, TypedDict
from uuid import UUID

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from hive_sight_advisor_api.adapters.treatment_suggestion_provider import (
    TreatmentSuggestionProvider,
)
from hive_sight_advisor_api.repositories.proposed_treatment_repository import (
    ProposedTreatment,
    ProposedTreatmentRepository,
)
from hive_sight_advisor_api.workflows.answer_query import Answer, AnswerQueryWorkflow

# A dedicated internal Workspace for agentic, app-to-app requests that have no real
# Beekeeper/Workspace context — see migrations/0006_slice_0008_system_workspace.sql
# and requirements/decision-log.md, "Agentic Treatment Plan Request Mechanism".
SYSTEM_WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000000001")


class TreatmentPlanState(TypedDict):
    hive_id: str
    jurisdiction_id: UUID
    query_text: str
    answer: Answer | None
    proposed_treatment_id: UUID | None


class TreatmentPlanWorkflow:
    """Recommend -> Suggest -> Wait -> Resume, per Slice 0008.

    The suspend in `_wait_and_resume` is only real because `checkpointer` is expected
    to be a Postgres-backed saver, not an in-memory one — see
    requirements/decision-log.md, "Agentic Treatment Plan Request Mechanism", point 4.
    """

    def __init__(
        self,
        answer_query_workflow: AnswerQueryWorkflow,
        treatment_suggestion_provider: TreatmentSuggestionProvider,
        proposed_treatment_repository: ProposedTreatmentRepository,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._answer_query_workflow = answer_query_workflow
        self._treatment_suggestion_provider = treatment_suggestion_provider
        self._proposed_treatment_repository = proposed_treatment_repository
        self._graph = self._build_graph().compile(checkpointer=checkpointer)

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(TreatmentPlanState)
        graph.add_node("recommend", self._recommend)
        graph.add_node("suggest", self._suggest)
        graph.add_node("wait_and_resume", self._wait_and_resume)
        graph.add_edge(START, "recommend")
        graph.add_conditional_edges(
            "recommend",
            lambda state: "suggest" if state["answer"].grounding_status != "ungrounded" else END,
            {"suggest": "suggest", END: END},
        )
        graph.add_edge("suggest", "wait_and_resume")
        graph.add_edge("wait_and_resume", END)
        return graph

    def _recommend(self, state: TreatmentPlanState) -> dict[str, Any]:
        answer = self._answer_query_workflow.answer_query(
            workspace_id=SYSTEM_WORKSPACE_ID,
            query_text=state["query_text"],
            jurisdiction_id=state["jurisdiction_id"],
        )
        return {"answer": answer}

    def _suggest(self, state: TreatmentPlanState) -> dict[str, Any]:
        answer = state["answer"]
        assert answer is not None
        self._treatment_suggestion_provider.suggest_treatment(state["hive_id"], answer.text)
        proposed_treatment = self._proposed_treatment_repository.save(
            hive_id=state["hive_id"],
            jurisdiction_id=state["jurisdiction_id"],
            answer_id=answer.id,
        )
        return {"proposed_treatment_id": proposed_treatment.id}

    def _wait_and_resume(self, state: TreatmentPlanState) -> dict[str, Any]:
        interrupt("awaiting-hivesight-completion")
        proposed_treatment_id = state["proposed_treatment_id"]
        assert proposed_treatment_id is not None
        self._proposed_treatment_repository.mark_completed(proposed_treatment_id)
        return {}

    def _thread_id(self, hive_id: str) -> str:
        return f"treatment-plan-{hive_id}"

    def request_treatment_plan(self, hive_id: str, jurisdiction_id: UUID, query_text: str) -> Answer:
        config = {"configurable": {"thread_id": self._thread_id(hive_id)}}
        result = self._graph.invoke(
            {
                "hive_id": hive_id,
                "jurisdiction_id": jurisdiction_id,
                "query_text": query_text,
                "answer": None,
                "proposed_treatment_id": None,
            },
            config=config,
        )
        answer = result["answer"]
        assert answer is not None
        return answer

    def confirm_completed(self, hive_id: str) -> ProposedTreatment | None:
        config = {"configurable": {"thread_id": self._thread_id(hive_id)}}
        state_before = self._graph.get_state(config)
        proposed_treatment_id = state_before.values.get("proposed_treatment_id")
        self._graph.invoke(Command(resume=True), config=config)
        if proposed_treatment_id is None:
            return None
        return self._proposed_treatment_repository.find_by_id(proposed_treatment_id)
