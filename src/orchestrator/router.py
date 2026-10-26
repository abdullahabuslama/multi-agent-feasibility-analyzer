"""Where the workflow goes after the review agent.

Two choices: send work back to the agents the reviewer named, or move on
to the next stage. The reviewer's verdict and the revision counter are
read from the blackboard; this file only decides.
"""

from src.memory import blackboard
from src.orchestrator.state import FeasibilityState


def needs_revision(state: FeasibilityState, max_revisions: int) -> bool:
    """True when the reviewer asked for changes and the limit is not reached yet."""
    validation = blackboard.read_validation(state)
    asked_for_changes = validation is not None and bool(validation.revision_requests)
    # The counter already includes the current request (see blackboard).
    return asked_for_changes and blackboard.read_revision_count(state) <= max_revisions


def route_after_review(
    state: FeasibilityState,
    *,
    stages_before_review: list[list[str]],
    next_stage: list[str],
    max_revisions: int,
) -> list[str]:
    """Names of the nodes to run next."""
    if not needs_revision(state, max_revisions):
        return next_stage
    requested = set(blackboard.read_validation(state).revision_requests)
    # Re-run only the earliest stage with a requested agent. Later stages
    # run again anyway, because the normal edges lead to them.
    for stage in stages_before_review:
        targets = [agent for agent in stage if agent in requested]
        if targets:
            return targets
    return next_stage
