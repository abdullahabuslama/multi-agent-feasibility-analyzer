"""Risk Analysis agent.

Goal: find the material risks and estimate their severity before
implementation. Runs after the technical, financial, and competitor
agents, so it can use their findings (`blackboard.read_findings`).

Responsibilities (proposal §9):
- Analyse technical, financial, operational, security, privacy,
  legal/compliance, AI, and market risks.
- Use the other agents' findings as risk inputs.
- Score probability and impact.
- Suggest mitigation strategies.
- Identify risks that depend on unresolved assumptions.

Output: an AgentFinding with a risk register: category, description,
likelihood, impact, severity, evidence, and mitigation.

It runs the shared analyst loop in `src/agents/analyst.py`. To return
more fields than AgentFinding has, subclass AgentFinding and set
`output_type` on this class.
"""

from src.agents.analyst import AnalystAgent


class RiskAgent(AnalystAgent):
    pass
