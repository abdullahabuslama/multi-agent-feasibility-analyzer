"""Supervisor (Orchestrator) agent.

Reads the business idea and writes a short brief for every agent in the
workflow. It does not choose the order of the work: that is fixed in
`config/tasks.yaml`, so the flow stays predictable and easy to test.

It is the one agent whose job is about the workflow itself, so it reads the
workflow config directly instead of receiving it.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import load_tasks_config
from src.agents.base import BaseAgent
from src.agents.request import format_request, idea_sections
from src.orchestrator.state import FeasibilityState, TaskPlan
from src.utils.llm import structured_output


class SupervisorAgent(BaseAgent):
    output_type = TaskPlan

    def analyze(self, state: FeasibilityState) -> TaskPlan:
        planner = structured_output(self.llm, TaskPlan)
        plan = planner.invoke(
            [SystemMessage(self.system_prompt), HumanMessage(self._request(state))]
        )
        # Keep only briefs for agents that really exist in the workflow.
        known = set(load_tasks_config().workflow.agents)
        return plan.model_copy(update={"briefs": [b for b in plan.briefs if b.agent in known]})

    def _request(self, state: FeasibilityState) -> str:
        config = load_tasks_config()
        agent_lines = "\n".join(
            f"- {name}: {config.tasks[name].description.strip() if name in config.tasks else ''}"
            for name in config.workflow.agents
        )
        sections = idea_sections(state["idea"])
        sections["Agents to brief (use these names exactly)"] = agent_lines
        return format_request(sections)
