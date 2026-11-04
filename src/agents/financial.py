"""Financial Analysis agent — not implemented yet.

Goal: decide if the idea makes economic sense under explicit assumptions.

Responsibilities (proposal §7):
- Estimate the initial implementation cost.
- Estimate recurring infrastructure, API, maintenance, and training cost.
- Estimate expected savings or revenue.
- Calculate ROI, payback period, and total cost of ownership.
- Show which assumptions have the largest effect on the result.

All important arithmetic must be done by deterministic code, not by the LLM.

Output: an AgentFinding with assumptions, cost breakdown, benefit estimate,
ROI, payback period, and confidence notes.
"""

from src.agents.base import BaseAgent, placeholder_finding
from src.orchestrator.state import AgentFinding, FeasibilityState


class FinancialAgent(BaseAgent):
    def analyze(self, state: FeasibilityState) -> AgentFinding:
        return placeholder_finding(self.name)
