"""The one place that runs the workflow graph.

`start()` runs it in a background thread and returns at once, for the
dashboard. `run_and_wait()` runs it and waits, for `POST /analyses`. Both go
through `_execute()`, which saves every event the graph emits and the final
state, so a run looks the same in the store whichever way it was started.
"""

import threading
from typing import Any

from langgraph.graph.state import CompiledStateGraph
from pydantic_core import to_jsonable_python

from src.orchestrator.events import EventKind, RunEvent, new_event
from src.orchestrator.state import BusinessIdea
from src.runs.store import RunStatus, RunStore
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RunService:
    def __init__(self, graph: CompiledStateGraph, store: RunStore) -> None:
        self.graph = graph
        self.store = store

    def start(self, idea: BusinessIdea) -> str:
        """Start a run in the background. Returns its id at once."""
        run = self.store.create_run(idea)
        threading.Thread(target=self._execute_in_background, args=(run.id, idea), daemon=True).start()
        return run.id

    def run_and_wait(self, idea: BusinessIdea) -> tuple[str, dict[str, Any]]:
        """Run to the end. Returns the run id and the final state."""
        run = self.store.create_run(idea)
        return run.id, self._execute(run.id, idea)

    def _execute_in_background(self, run_id: str, idea: BusinessIdea) -> None:
        try:
            self._execute(run_id, idea)
        except Exception:
            pass  # already saved as a failed run and logged by _execute

    def _execute(self, run_id: str, idea: BusinessIdea) -> dict[str, Any]:
        self.store.add_event(run_id, new_event(EventKind.RUN_STARTED))
        final_state: dict[str, Any] = {}
        try:
            # "custom" chunks are the RunEvents the nodes emit; "values" is the
            # state after each step, so the last one is the final state.
            for mode, chunk in self.graph.stream(
                {"idea": idea},
                config={"configurable": {"thread_id": run_id}},
                stream_mode=["custom", "values"],
            ):
                if mode == "custom" and isinstance(chunk, RunEvent):
                    self.store.add_event(run_id, chunk)
                elif mode == "values":
                    final_state = chunk
        except Exception as error:
            logger.exception("Run %s failed", run_id)
            self.store.add_event(run_id, new_event(EventKind.RUN_FAILED, error=str(error)))
            self.store.finish_run(run_id, RunStatus.FAILED, error=str(error))
            raise
        self.store.add_event(run_id, new_event(EventKind.RUN_FINISHED))
        self.store.finish_run(run_id, RunStatus.DONE, result=to_jsonable_python(final_state))
        return final_state
