"""Validation / Critic agent — not implemented yet.

Goal: check the findings before the report is written.

Responsibilities (proposal §5 and §12):
- Check evidence behind each important claim.
- Find contradictions between agents.
- Re-check calculations.
- Surface missing or hidden assumptions and check completeness.
- Name the agents that must redo their work in `revision_requests`.
  The workflow sends work back to them (up to `max_revisions` times,
  set in `config/tasks.yaml`).

Output: a ValidationResult.
"""

from src.agents.base import BaseAgent
from src.orchestrator.state import FeasibilityState, ValidationResult


class ValidatorAgent(BaseAgent):
    output_type = ValidationResult

    def analyze(self, state: FeasibilityState) -> ValidationResult:
        return ValidationResult(
            approved=True,
            summary="The validator agent is not implemented yet. Nothing was checked.",
        )
