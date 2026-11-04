"""The contract every agent follows, and the factory that builds agents.

An agent is built from its entry in `config/agents.yaml`. `build_agent`
reads that entry, the system prompt file, the agent's task, and its tools,
and hands them to the agent. The agent itself reads no files and no config,
so it can also be built in a test with any prompt or tools.

Each agent implements one method, `analyze(state)`, and returns one output
model. `run(state)` is what the graph calls: it runs `analyze`, checks the
output, and posts it on the blackboard. Agents never write the state
themselves.
"""

import importlib
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from config.models import AgentConfig, TaskConfig
from config.settings import PROMPTS_DIR, load_agents_config, load_tasks_config
from src.memory import blackboard
from src.orchestrator.state import AgentFinding, FeasibilityState
from src.tools import resolve_tools
from src.utils.guardrails import ensure_output
from src.utils.llm import get_chat_model


class BaseAgent(ABC):
    """Parent class of all agents.

    Attributes ready for subclasses: `name`, `config` (its agents.yaml
    entry: role, goal, backstory, ...), `system_prompt`, `task` (its
    tasks.yaml entry, or None), `tools`, and `llm`.
    """

    # What `analyze` returns. Analysts return an AgentFinding; the supervisor,
    # validator, and reporter override this with their own model.
    output_type: ClassVar[type[BaseModel]] = AgentFinding

    def __init__(
        self,
        name: str,
        config: AgentConfig,
        system_prompt: str,
        task: TaskConfig | None,
        tools: list[BaseTool],
    ) -> None:
        self.name = name
        self.config = config
        self.system_prompt = system_prompt
        self.task = task
        self.tools = tools
        self._llm: BaseChatModel | None = None

    @property
    def llm(self) -> BaseChatModel:
        # Created on first use, so building the graph needs no API key.
        if self._llm is None:
            self._llm = get_chat_model(self.config.llm)
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
    module_path, class_name = config.class_path.rsplit(".", 1)
    agent_class = getattr(importlib.import_module(module_path), class_name)
    return agent_class(
        name=name,
        config=config,
        system_prompt=(PROMPTS_DIR / config.prompt_file).read_text(encoding="utf-8"),
        task=load_tasks_config().tasks.get(name),
        tools=resolve_tools(config.tools),
    )
