"""Shared test fixtures. Tests use no network and no API key.

- `fake_llm`: every agent gets a fake chat model with canned answers.
- `memory_store`: Qdrant runs in memory with fake embeddings, so no model
  is downloaded and nothing is written to disk.
"""

from typing import Any

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from qdrant_client import QdrantClient

from src.agents import base as agents_base
from src.memory import long_term
from src.orchestrator.state import AgentBrief, BusinessIdea, TaskPlan

SAMPLE_IDEA = BusinessIdea(
    idea="Add an AI chat assistant that answers 'Where is my order?' questions.",
    context="Pilot budget around EGP 1.5 million.",
)

FAKE_PLAN = TaskPlan(
    summary="Decide whether an AI order-tracking assistant is worth a pilot.",
    briefs=[
        AgentBrief(agent="technical", instructions="Check the Orders API and help desk."),
        AgentBrief(agent="financial", instructions="Compare cost to support savings."),
        AgentBrief(agent="not_an_agent", instructions="Should be dropped."),
    ],
)


class FakeChatModel:
    """Stands in for a real chat model. Returns a canned answer per output model."""

    def __init__(self, answers: dict[type[BaseModel], BaseModel]) -> None:
        self.answers = answers

    def with_structured_output(self, schema: type[BaseModel], **_: Any) -> RunnableLambda:
        return RunnableLambda(lambda _messages: self.answers[schema])


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeChatModel:
    model = FakeChatModel({TaskPlan: FAKE_PLAN})
    monkeypatch.setattr(agents_base, "get_chat_model", lambda _params=None: model)
    return model


@pytest.fixture
def memory_store(monkeypatch: pytest.MonkeyPatch) -> QdrantClient:
    client = QdrantClient(":memory:")
    embeddings = DeterministicFakeEmbedding(size=64)
    monkeypatch.setattr(long_term, "get_client", lambda: client)
    monkeypatch.setattr(long_term, "get_embeddings", lambda: embeddings)
    return client
