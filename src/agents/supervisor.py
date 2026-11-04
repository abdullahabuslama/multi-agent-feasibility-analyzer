"""Supervisor (Orchestrator) agent.

Reads the business idea and writes a short brief for every agent in the
workflow. It does not choose the order of the work: that is fixed in
`config/tasks.yaml`, so the flow stays predictable and easy to test.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import load_tasks_config, workflow_agents
from src.agents.base import BaseAgent
from src.orchestrator.state import FeasibilityState, TaskPlan


class SupervisorAgent(BaseAgent):
    output_type = TaskPlan

    def analyze(self, state: FeasibilityState) -> TaskPlan:
        planner = self.llm.with_structured_output(TaskPlan)
        plan = planner.invoke(
            [SystemMessage(self.system_prompt), HumanMessage(self._request(state))]
        )
        # Keep only briefs for agents that really exist in the workflow.
        known = set(workflow_agents())
        return plan.model_copy(update={"briefs": [b for b in plan.briefs if b.agent in known]})

    def _request(self, state: FeasibilityState) -> str:
        idea = state["idea"]
        tasks = load_tasks_config()["tasks"]
        agent_lines = "\n".join(
            f"- {name}: {tasks.get(name, {}).get('description', '').strip()}"
            for name in workflow_agents()
        )
        context = idea.context or "None given."
        return (
            f"Business idea:\n{idea.idea}\n\n"
            f"Extra context from the user:\n{context}\n\n"
            f"Agents to brief (use these names exactly):\n{agent_lines}"
        )
