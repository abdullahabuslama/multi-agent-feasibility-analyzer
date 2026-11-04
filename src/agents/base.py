"""The contract every agent follows.

An agent is built from its entry in `config/agents.yaml`. It gets its
system prompt, its tools, and (when first used) its LLM from there.

Each agent implements one method, `analyze(state)`, and returns one output
model. `run(state)` is what the graph calls: it runs `analyze`, checks the
output, and posts it on the blackboard. Agents never write the state
themselves.
"""

import importlib
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from config.settings import PROMPTS_DIR, load_agents_config, load_tasks_config
from src.memory import blackboard
from src.orchestrator.state import AgentFinding, FeasibilityState, FindingStatus
from src.tools import resolve_tools
from src.utils.guardrails import ensure_output
from src.utils.llm import get_chat_model


class BaseAgent(ABC):
    """Parent class of all agents.

    Attributes ready for subclasses: `name`, `role`, `goal`, `backstory`,
    `system_prompt`, `task` (its entry in tasks.yaml), `tools`, and `llm`.
    """

    # What `analyze` returns. Analysts return an AgentFinding; the supervisor,
    # validator, and reporter override this with their own model.
    output_type: ClassVar[type[BaseModel]] = AgentFinding

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.role: str = config["role"]
        self.goal: str = config["goal"]
        self.backstory: str = config.get("backstory", "")
        self.system_prompt = (PROMPTS_DIR / config["prompt_file"]).read_text(encoding="utf-8")
        self.task: dict[str, str] = load_tasks_config()["tasks"].get(name, {})
        self.tools = resolve_tools(config.get("tools", []))
        self._llm_params: dict[str, Any] = config.get("llm", {})
        self._llm: BaseChatModel | None = None

    @property
    def llm(self) -> BaseChatModel:
        # Created on first use, so building the graph needs no API key.
        if self._llm is None:
            self._llm = get_chat_model(self._llm_params)
        return self._llm

    @abstractmethod
    def analyze(self, state: FeasibilityState) -> BaseModel:
        """Do this agent's work and return an instance of `output_type`."""

    def run(self, state: FeasibilityState) -> dict[str, Any]:
        """The graph node: analyze, check, and post the result."""
        output = ensure_output(self.analyze(state), self.name, self.output_type)
        return blackboard.post(output, state)


def build_agent(name: str) -> BaseAgent:
    """Create the agent declared as `name` in `config/agents.yaml`."""
    config = load_agents_config()[name]
    module_path, class_name = config["class_path"].rsplit(".", 1)
    agent_class = getattr(importlib.import_module(module_path), class_name)
    return agent_class(name, config)


def placeholder_finding(agent_name: str) -> AgentFinding:
    """The finding an analyst returns until its owner builds it."""
    return AgentFinding(
        agent=agent_name,
        status=FindingStatus.PENDING,
        summary=f"The {agent_name} agent is not implemented yet.",
    )
