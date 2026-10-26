"""Shared state of one analysis run, and the data models that live in it.

Every agent reads from and writes to this state. Agents do not write the
keys by hand: they return one of the output models below, and
`src/memory/blackboard.py` stores it in the right place.
"""

from enum import StrEnum
from typing import Annotated, TypedDict

from pydantic import BaseModel, ConfigDict, Field

MIN_IDEA_LENGTH = 10
MAX_IDEA_LENGTH = 4000


class FeasibilityState(TypedDict, total=False):
    """The state LangGraph passes from node to node."""

    idea: "BusinessIdea"
    plan: "TaskPlan"
    # Several agents run in parallel and each adds its own finding,
    # so new findings are merged into the dict instead of replacing it.
    findings: Annotated[dict[str, "AgentFinding"], lambda old, new: {**old, **new}]
    validation: "ValidationResult"
    revision_count: int
    report: "FinalReport"


class BusinessIdea(BaseModel):
    """The input: the idea to evaluate and optional extra context."""

    model_config = ConfigDict(str_strip_whitespace=True)

    idea: str = Field(min_length=MIN_IDEA_LENGTH, max_length=MAX_IDEA_LENGTH)
    context: str | None = Field(
        default=None,
        description="Optional assumptions or details from the user, e.g. budget or timeline.",
    )


class AgentBrief(BaseModel):
    """What the supervisor asks one agent to focus on."""

    agent: str = Field(description="Agent name, exactly as listed, e.g. 'technical'.")
    instructions: str = Field(description="What this agent should focus on for this idea.")


class TaskPlan(BaseModel):
    """The supervisor's output: its reading of the idea plus one brief per agent."""

    summary: str = Field(description="Short restatement of the idea and what must be decided.")
    briefs: list[AgentBrief]


class FindingStatus(StrEnum):
    PENDING = "pending"  # agent not implemented yet, or it had nothing to report
    DONE = "done"
    FAILED = "failed"  # agent tried but could not finish, e.g. a tool was down


class Evidence(BaseModel):
    """A source that supports a claim: a company document or a web page."""

    source: str = Field(description="File name or URL.")
    snippet: str = Field(description="The part of the source that supports the claim.")


class AgentFinding(BaseModel):
    """The output of one analyst agent.

    Need more fields for your agent (a cost table, a risk register)?
    Subclass this model in your agent file and add them.
    """

    agent: str
    status: FindingStatus
    summary: str
    score: float | None = Field(default=None, ge=0, le=10)
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """The review agent's verdict on the findings."""

    approved: bool
    summary: str
    issues: list[str] = Field(default_factory=list)
    revision_requests: list[str] = Field(
        default_factory=list,
        description="Names of the agents that must redo their work.",
    )


class FinalReport(BaseModel):
    """The report shown to management."""

    markdown: str
