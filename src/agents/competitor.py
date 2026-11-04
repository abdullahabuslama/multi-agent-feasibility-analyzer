"""Competitor Analysis agent.

Goal: understand the market around the idea and the company's position in it.

Responsibilities (proposal §8):
- Identify direct and indirect competitors.
- Compare features, target customers, pricing, and positioning.
- Identify market gaps and possible differentiation.
- Flag competitor information that changes fast or is uncertain.

Output: an AgentFinding with the competitive landscape, a comparison
summary, differentiation opportunities, and key market observations.

It runs the shared analyst loop in `src/agents/analyst.py`. To return
more fields than AgentFinding has, subclass AgentFinding and set
`output_type` on this class.
"""

from src.agents.analyst import AnalystAgent


class CompetitorAgent(AnalystAgent):
    pass
