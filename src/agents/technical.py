"""Technical Feasibility agent.

Goal: decide if the company can realistically build the idea.

Responsibilities (proposal §6):
- Identify required technologies and infrastructure.
- Check dependencies on existing systems and APIs.
- Identify data requirements and security constraints.
- Estimate implementation complexity and major technical dependencies.
- Surface missing technical information that needs more investigation.

Output: an AgentFinding with requirements, dependencies, constraints,
key assumptions, and a feasibility score (0–10).

It runs the shared analyst loop in `src/agents/analyst.py`. To return
more fields than AgentFinding has, subclass AgentFinding and set
`output_type` on this class.
"""

from src.agents.analyst import AnalystAgent


class TechnicalAgent(AnalystAgent):
    pass
