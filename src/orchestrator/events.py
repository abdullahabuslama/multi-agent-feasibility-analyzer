"""Live events of a run: what each agent is doing, as it happens.

The graph and the agents call `emit()`. During a run, LangGraph hands each
event to whoever streams the graph (`RunService` in `src/runs/service.py`),
which saves it so the dashboard can show it. Outside a run, for example in
a unit test that calls `agent.analyze()` directly, `emit()` does nothing.

This is the only file that knows how events travel through LangGraph, so
agents can report what they do without learning LangGraph.
"""

import functools
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field
from pydantic_core import to_jsonable_python


class EventKind(StrEnum):
    RUN_STARTED = "run_started"
    AGENT_STARTED = "agent_started"
    AGENT_FINISHED = "agent_finished"  # detail.output: the state update the agent posted
    AGENT_FAILED = "agent_failed"
    LLM_CALLED = "llm_called"  # detail.purpose: "research" or "final_answer"
    TOOL_CALLED = "tool_called"  # detail: tool, args
    TOOL_RETURNED = "tool_returned"  # detail: tool, ok, preview, characters
    RUN_FINISHED = "run_finished"
    RUN_FAILED = "run_failed"


# After one of these, a run sends no more events.
FINAL_EVENT_KINDS = frozenset({EventKind.RUN_FINISHED, EventKind.RUN_FAILED})


class RunEvent(BaseModel):
    seq: int = Field(default=0, description="Position in the run, from 1. Set when the event is saved.")
    kind: EventKind
    at: datetime
    agent: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


def new_event(kind: EventKind, agent: str | None = None, **detail: Any) -> RunEvent:
    # Stored as plain JSON values, so saving and sending the event cannot fail later.
    return RunEvent(kind=kind, at=datetime.now(UTC), agent=agent, detail=to_jsonable_python(detail))


def emit(kind: EventKind, agent: str | None = None, **detail: Any) -> None:
    """Report an event of the running graph. Does nothing outside a graph run."""
    try:
        writer = get_stream_writer()
    except RuntimeError:
        return
    writer(new_event(kind, agent, **detail))


def publish_node_events(agent: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for a graph node: emit when the agent starts, finishes, or fails."""

    def decorator(node: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(node)
        def published(*args: Any, **kwargs: Any) -> Any:
            emit(EventKind.AGENT_STARTED, agent)
            try:
                update = node(*args, **kwargs)
            except Exception as error:
                emit(EventKind.AGENT_FAILED, agent, error=str(error))
                raise
            emit(EventKind.AGENT_FINISHED, agent, output=update)
            return update

        return published

    return decorator
