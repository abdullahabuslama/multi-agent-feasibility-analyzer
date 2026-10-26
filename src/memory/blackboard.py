"""The blackboard: the one place that writes agent outputs into the shared state.

Think of a whiteboard in a meeting room. Each agent pins its result on it,
and every other agent can read what is there. The LangGraph state is the
board; this file decides where each kind of result is pinned.

Agents never write state keys themselves. They return an output model and
`post()` turns it into a state update. Readers below give agents a safe way
to read what others posted.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from src.orchestrator.state import (
    AgentFinding,
    FeasibilityState,
    FinalReport,
    TaskPlan,
    ValidationResult,
)


def post(output: BaseModel, state: FeasibilityState) -> dict[str, Any]:
    """Return the state update that stores `output` on the board."""
    for output_type in type(output).__mro__:
        writer = _WRITERS.get(output_type)
        if writer:
            return writer(output, state)
    raise TypeError(f"The blackboard has no place for {type(output).__name__}.")


def read_findings(
    state: FeasibilityState, agents: list[str] | None = None
) -> dict[str, AgentFinding]:
    """Findings posted so far, optionally only those of the given agents."""
    findings = state.get("findings", {})
    if agents is None:
        return dict(findings)
    return {name: findings[name] for name in agents if name in findings}


def read_brief(state: FeasibilityState, agent: str) -> str | None:
    """The supervisor's instructions for one agent, if it wrote any."""
    plan = state.get("plan")
    if plan is None:
        return None
    return next((brief.instructions for brief in plan.briefs if brief.agent == agent), None)


def read_validation(state: FeasibilityState) -> ValidationResult | None:
    return state.get("validation")


def read_revision_count(state: FeasibilityState) -> int:
    return state.get("revision_count", 0)


def _write_plan(plan: TaskPlan, state: FeasibilityState) -> dict[str, Any]:
    return {"plan": plan}


def _write_finding(finding: AgentFinding, state: FeasibilityState) -> dict[str, Any]:
    return {"findings": {finding.agent: finding}}


def _write_validation(result: ValidationResult, state: FeasibilityState) -> dict[str, Any]:
    update: dict[str, Any] = {"validation": result}
    if result.revision_requests:
        # Counted here, when the request is made, so the router only reads it.
        update["revision_count"] = read_revision_count(state) + 1
    return update


def _write_report(report: FinalReport, state: FeasibilityState) -> dict[str, Any]:
    return {"report": report}


# Which writer handles which output model. A new kind of output = one new line.
_WRITERS: dict[type, Callable[[Any, FeasibilityState], dict[str, Any]]] = {
    TaskPlan: _write_plan,
    AgentFinding: _write_finding,
    ValidationResult: _write_validation,
    FinalReport: _write_report,
}
