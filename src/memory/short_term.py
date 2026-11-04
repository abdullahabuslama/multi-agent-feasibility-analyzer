"""Short-term memory: saves the state of each run while the app is running.

LangGraph calls this a checkpointer. Every run gets a `thread_id`, and the
state after each step is saved under it. The in-memory version is lost
when the app stops, which is enough for now.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver


def get_checkpointer() -> BaseCheckpointSaver:
    return InMemorySaver()
