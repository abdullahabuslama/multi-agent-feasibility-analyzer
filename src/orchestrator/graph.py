"""Builds the LangGraph workflow from `config/tasks.yaml`.

The graph is not written by hand. It is read from the config:

    START -> entry agent -> stage 1 (in parallel) -> stage 2 -> ... -> END

Every agent in a stage connects to every agent in the next stage. The
review agent is the exception: after it, the router decides whether to
send work back or to move on. The rules for a valid workflow (for example,
the review agent is alone in its stage) are checked in `config/models.py`.
"""

from functools import partial

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from config.models import WorkflowConfig
from config.settings import load_tasks_config
from src.agents import build_agent
from src.orchestrator.router import route_after_review
from src.orchestrator.state import FeasibilityState
from src.utils.logger import trace_node


def build_graph(checkpointer: BaseCheckpointSaver | None = None) -> CompiledStateGraph:
    workflow = load_tasks_config().workflow
    stages = workflow.stages

    graph = StateGraph(FeasibilityState)
    for name in [workflow.entry, *workflow.agents]:
        graph.add_node(name, trace_node(name)(build_agent(name).run))

    graph.add_edge(START, workflow.entry)
    _connect(graph, [workflow.entry], stages[0])
    for index, stage in enumerate(stages):
        next_stage = stages[index + 1] if index + 1 < len(stages) else [END]
        if index == workflow.review_stage_index:
            _add_review_router(graph, workflow, next_stage)
        else:
            _connect(graph, stage, next_stage)

    return graph.compile(checkpointer=checkpointer)


def _connect(graph: StateGraph, sources: list[str], targets: list[str]) -> None:
    for source in sources:
        for target in targets:
            graph.add_edge(source, target)


def _add_review_router(graph: StateGraph, workflow: WorkflowConfig, next_stage: list[str]) -> None:
    stages_before_review = workflow.stages[: workflow.review_stage_index]
    router = partial(
        route_after_review,
        stages_before_review=stages_before_review,
        next_stage=next_stage,
        max_revisions=workflow.review.max_revisions,
    )
    possible_targets = [agent for stage in stages_before_review for agent in stage] + next_stage
    graph.add_conditional_edges(workflow.review.agent, router, possible_targets)
