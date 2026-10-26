"""Competitor Analysis agent — not implemented yet.

Goal: understand the market around the idea and the company's position in it.

Responsibilities (proposal §8):
- Identify direct and indirect competitors.
- Compare features, target customers, pricing, and positioning.
- Identify market gaps and possible differentiation.
- Flag competitor information that changes fast or is uncertain.

Output: an AgentFinding with the competitive landscape, a comparison
summary, differentiation opportunities, and key market observations.
"""

from src.agents.base import BaseAgent, placeholder_finding
from src.orchestrator.state import AgentFinding, FeasibilityState


class CompetitorAgent(BaseAgent):
    def analyze(self, state: FeasibilityState) -> AgentFinding:
        return placeholder_finding(self.name)
