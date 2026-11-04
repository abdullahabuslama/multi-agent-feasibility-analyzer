"""Response models of the HTTP API: the public contract clients rely on.

They stay separate from the internal models on purpose: the state and the
store may grow internal fields that clients should not see. The dashboard's
TypeScript types are generated from these models (`npm run gen:api`).
"""

from datetime import datetime

from pydantic import BaseModel, SerializeAsAny

from src.orchestrator.events import RunEvent
from src.orchestrator.state import (
    AgentFinding,
    BusinessIdea,
    FinalReport,
    TaskPlan,
    ValidationResult,
)
from src.runs.store import RunStatus


class AnalysisResponse(BaseModel):
    """The run's id plus the final state.

    The fields have the same names as the keys of `FeasibilityState`, so the
    state is passed in as it is. Unknown keys are ignored.
    """

    thread_id: str
    plan: TaskPlan | None = None
    # SerializeAsAny keeps extra fields of agent-specific finding subclasses.
    findings: dict[str, SerializeAsAny[AgentFinding]] = {}
    validation: ValidationResult | None = None
    revision_count: int = 0
    report: FinalReport | None = None


class RunCreated(BaseModel):
    run_id: str


class RunSummary(BaseModel):
    id: str
    idea: BusinessIdea
    status: RunStatus
    created_at: datetime
    finished_at: datetime | None = None
    error: str | None = None


class RunDetail(RunSummary):
    """A run with every event so far. `result` is set once the run is done.

    The events hold each agent's full output, including extra fields of
    finding subclasses. `result` holds only the standard fields.
    """

    events: list[RunEvent]
    result: AnalysisResponse | None = None


class AgentView(BaseModel):
    name: str
    role: str
    goal: str
    tools: list[str]


class WorkflowView(BaseModel):
    """The shape of the workflow, so the dashboard draws it from the config."""

    entry: str
    stages: list[list[str]]
    review_agent: str
    max_revisions: int
    agents: list[AgentView]
