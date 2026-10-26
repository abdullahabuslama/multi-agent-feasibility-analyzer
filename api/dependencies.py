"""Shared objects the API endpoints receive through FastAPI `Depends`."""

from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from src.memory.short_term import get_checkpointer
from src.orchestrator.graph import build_graph


@lru_cache
def get_graph() -> CompiledStateGraph:
    """The workflow, built once when the first request arrives."""
    return build_graph(checkpointer=get_checkpointer())
