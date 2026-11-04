"""Shared objects the API endpoints receive through FastAPI `Depends`."""

from functools import lru_cache

from fastapi import Depends
from langgraph.graph.state import CompiledStateGraph

from config.settings import get_settings
from src.memory.short_term import get_checkpointer
from src.orchestrator.graph import build_graph
from src.runs.service import RunService
from src.runs.store import RunStore


@lru_cache
def get_graph() -> CompiledStateGraph:
    """The workflow, built once when the first request arrives."""
    return build_graph(checkpointer=get_checkpointer())


@lru_cache
def get_run_store() -> RunStore:
    """The run history, opened once. Runs a stopped server left unfinished are marked failed."""
    store = RunStore(get_settings().runs_db_path)
    store.fail_unfinished_runs()
    return store


def get_run_service(
    graph: CompiledStateGraph = Depends(get_graph), store: RunStore = Depends(get_run_store)
) -> RunService:
    return RunService(graph, store)
