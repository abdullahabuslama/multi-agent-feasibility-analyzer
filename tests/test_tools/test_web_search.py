from types import SimpleNamespace
from typing import Any

import pytest

import src.tools.web_search as web_search_module
from src.tools import TOOL_REGISTRY
from src.tools.web_search import web_search

PAYMOB_RESULT = SimpleNamespace(
    url="https://paymob.com/en/pricing",
    title="Paymob | Pricing",
    published_date="2026-10-29T00:00:00.000Z",
    highlights=["Local cards: 2.75% + EGP 3 per transaction."],
)


class FakeExa:
    """Stands in for the Exa client. Returns canned results and keeps the last call."""

    def __init__(self, results: list[Any]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def search(self, query: str, **options: Any) -> SimpleNamespace:
        self.calls.append((query, options))
        return SimpleNamespace(results=self.results)


@pytest.fixture
def fake_exa(monkeypatch: pytest.MonkeyPatch) -> FakeExa:
    client = FakeExa([PAYMOB_RESULT])
    monkeypatch.setattr(web_search_module, "get_exa_client", lambda: client)
    return client


def test_result_starts_with_its_url_so_it_can_be_cited(fake_exa: FakeExa) -> None:
    result = web_search.invoke({"query": "Paymob transaction fees Egypt"})

    assert result.startswith("[source: https://paymob.com/en/pricing]")
    assert "(published 2026-10-29)" in result
    assert "2.75% + EGP 3" in result


def test_search_asks_exa_for_matching_passages(fake_exa: FakeExa) -> None:
    web_search.invoke({"query": "Paymob transaction fees Egypt"})

    query, options = fake_exa.calls[0]
    assert query == "Paymob transaction fees Egypt"
    assert options["contents"] == {"highlights": {"max_characters": web_search_module.CHARACTERS_PER_RESULT}}


def test_no_results_says_so(fake_exa: FakeExa) -> None:
    fake_exa.results = []

    assert web_search.invoke({"query": "nothing matches"}) == "No matching web pages found."


def test_missing_api_key_fails_with_a_clear_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(web_search_module, "get_settings", lambda: SimpleNamespace(exa_api_key=""))
    web_search_module.get_exa_client.cache_clear()

    with pytest.raises(RuntimeError, match="EXA_API_KEY"):
        web_search_module.get_exa_client()


def test_web_search_tool_is_registered() -> None:
    assert "web_search" in TOOL_REGISTRY
