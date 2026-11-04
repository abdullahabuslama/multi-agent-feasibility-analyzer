"""Financial Analysis agent.

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

It runs the shared analyst loop in `src/agents/analyst.py`. To return
more fields than AgentFinding has, subclass AgentFinding and set
`output_type` on this class.
"""

from src.agents.analyst import AnalystAgent


class FinancialAgent(AnalystAgent):
    pass
