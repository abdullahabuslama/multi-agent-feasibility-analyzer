"""Typed shape of the two YAML config files.

`config/settings.py` loads the files into these models, so a missing key, a
misspelled key, or a broken workflow fails at load time with a clear message.
It does not fail later, in the middle of a run. Code reads attributes
(`workflow.review.max_revisions`), never raw dictionary keys.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    # An unknown key in the YAML is almost always a typo, so it is an error.
    model_config = ConfigDict(extra="forbid", frozen=True)


class AgentConfig(_StrictModel):
    """One entry of `config/agents.yaml`."""

    class_path: str
    role: str
    goal: str
    backstory: str = ""
    prompt_file: str
    tools: list[str] = Field(default_factory=list)
    llm: dict[str, Any] = Field(default_factory=dict)


class TaskConfig(_StrictModel):
    """What one agent is asked to do, from `tasks:` in `config/tasks.yaml`."""

    description: str
    expected_output: str


class ReviewConfig(_StrictModel):
    agent: str
    max_revisions: int = Field(ge=0)


class WorkflowConfig(_StrictModel):
    """The order of the work, from `workflow:` in `config/tasks.yaml`."""

    entry: str
    stages: list[list[str]] = Field(min_length=1)
    review: ReviewConfig

    @property
    def agents(self) -> list[str]:
        """Every agent in the stages, in order. The entry agent is not included."""
        return [name for stage in self.stages for name in stage]

    @property
    def review_stage_index(self) -> int:
        return next(index for index, stage in enumerate(self.stages) if self.review.agent in stage)

    @model_validator(mode="after")
    def _check_stages(self) -> "WorkflowConfig":
        if len(set(self.agents)) != len(self.agents):
            raise ValueError("An agent appears in more than one workflow stage.")
        if self.review.agent not in self.agents:
            raise ValueError(f"The review agent '{self.review.agent}' is not in any workflow stage.")
        if len(self.stages[self.review_stage_index]) > 1:
            raise ValueError(f"The review agent '{self.review.agent}' must be alone in its stage.")
        return self


class TasksConfig(_StrictModel):
    """The whole of `config/tasks.yaml`."""

    workflow: WorkflowConfig
    tasks: dict[str, TaskConfig] = Field(default_factory=dict)
