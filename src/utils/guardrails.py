"""Checks on what agents return, before it reaches the shared state.

The input idea is checked by its own model (`BusinessIdea` in
`src/orchestrator/state.py`), so this file only guards the outputs.
"""

from pydantic import BaseModel

from src.orchestrator.state import AgentFinding


class GuardrailError(ValueError):
    """An agent returned something the workflow cannot use."""


def ensure_output(output: object, agent_name: str, expected_type: type[BaseModel]) -> BaseModel:
    """Fail loudly if an agent returns the wrong type or signs a finding with another name."""
    if not isinstance(output, expected_type):
        raise GuardrailError(
            f"Agent '{agent_name}' must return {expected_type.__name__}, "
            f"got {type(output).__name__}."
        )
    if isinstance(output, AgentFinding) and output.agent != agent_name:
        raise GuardrailError(
            f"Agent '{agent_name}' returned a finding signed as '{output.agent}'."
        )
    return output
