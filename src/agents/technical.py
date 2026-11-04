"""Technical Feasibility agent — not implemented yet.

Goal: decide if the company can realistically build the idea.

Responsibilities (proposal §6):
- Identify required technologies and infrastructure.
- Check dependencies on existing systems and APIs.
- Identify data requirements and security constraints.
- Estimate implementation complexity and major technical dependencies.
- Surface missing technical information that needs more investigation.

Output: an AgentFinding with requirements, dependencies, constraints,
key assumptions, and a feasibility score (0–10).
"""

from src.agents.base import BaseAgent, placeholder_finding
from src.orchestrator.state import AgentFinding, FeasibilityState


class TechnicalAgent(BaseAgent):
    def analyze(self, state: FeasibilityState) -> AgentFinding:
        return placeholder_finding(self.name)
