from __future__ import annotations

from dataclasses import dataclass
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

# 3 revisions on top of the original suggestion (4 suggestions total, ever) — see
# requirements/decision-log.md, "Reject-And-Revise Treatment Plan Mechanism", point 8.
MAX_REVISIONS = 3


class TreatmentPlanState(TypedDict):
    hive_id: str
    jurisdiction_id: UUID
    query_text: str
    rejection_reason: str | None
    answer: Answer | None
    proposed_treatment_id: UUID | None
    revision_count: int
    last_action: str | None


@dataclass(frozen=True)
class RejectionOutcome:
    answer: Answer
    revision_exhausted: bool


class TreatmentPlanWorkflow:
    """Recommend -> Suggest -> Wait -> Resume, per Slice 0008; Slice 0009 adds a real
    cycle back from Wait to Recommend on rejection, capped at MAX_REVISIONS.

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
        graph.add_conditional_edges(
            "wait_and_resume",
            lambda state: "recommend" if state.get("last_action") == "reject" else END,
            {"recommend": "recommend", END: END},
        )
        return graph

    def _recommend(self, state: TreatmentPlanState) -> dict[str, Any]:
        query_text = state["query_text"]
        reason = state.get("rejection_reason")
        if reason:
            query_text = (
                f"{query_text}\n\nA previously suggested treatment was rejected because: "
                f"{reason}. Suggest an alternative that avoids this."
            )
        answer = self._answer_query_workflow.answer_query(
            workspace_id=SYSTEM_WORKSPACE_ID,
            query_text=query_text,
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
            supersedes_proposed_treatment_id=state.get("proposed_treatment_id"),
        )
        return {"proposed_treatment_id": proposed_treatment.id}

    def _wait_and_resume(self, state: TreatmentPlanState) -> dict[str, Any]:
        resume_value = interrupt("awaiting-hivesight-response")
        proposed_treatment_id = state["proposed_treatment_id"]
        assert proposed_treatment_id is not None
        if resume_value["action"] == "accept":
            self._proposed_treatment_repository.mark_completed(proposed_treatment_id)
            return {"last_action": "accept"}
        self._proposed_treatment_repository.mark_rejected(proposed_treatment_id)
        return {
            "last_action": "reject",
            "rejection_reason": resume_value["reason"],
            "revision_count": state.get("revision_count", 0) + 1,
        }

    def _thread_id(self, hive_id: str) -> str:
        return f"treatment-plan-{hive_id}"

    def request_treatment_plan(self, hive_id: str, jurisdiction_id: UUID, query_text: str) -> Answer:
        config = {"configurable": {"thread_id": self._thread_id(hive_id)}}
        result = self._graph.invoke(
            {
                "hive_id": hive_id,
                "jurisdiction_id": jurisdiction_id,
                "query_text": query_text,
                "rejection_reason": None,
                "answer": None,
                "proposed_treatment_id": None,
                "revision_count": 0,
                "last_action": None,
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
        self._graph.invoke(Command(resume={"action": "accept"}), config=config)
        if proposed_treatment_id is None:
            return None
        return self._proposed_treatment_repository.find_by_id(proposed_treatment_id)

    def reject_treatment(self, hive_id: str, reason: str) -> RejectionOutcome | None:
        config = {"configurable": {"thread_id": self._thread_id(hive_id)}}
        state_before = self._graph.get_state(config)
        proposed_treatment_id = state_before.values.get("proposed_treatment_id")
        if proposed_treatment_id is None:
            return None

        revision_count = state_before.values.get("revision_count", 0)
        if revision_count >= MAX_REVISIONS:
            answer = state_before.values.get("answer")
            assert answer is not None
            return RejectionOutcome(answer=answer, revision_exhausted=True)

        result = self._graph.invoke(Command(resume={"action": "reject", "reason": reason}), config=config)
        answer = result["answer"]
        assert answer is not None
        return RejectionOutcome(answer=answer, revision_exhausted=False)
