"""The web search tool, backed by Exa (https://exa.ai).

Agents use it for public, current facts that the company documents do not
have: technical documentation, public prices, competitors, regulations, and
incidents. Why Exa was picked is in `docs/research/web_search_selection.md`.

Every result keeps its URL, so findings can cite it as `Evidence`.
"""

from functools import lru_cache

from exa_py import Exa
from exa_py.api import Result

from config.settings import get_settings
from src.tools.base import register_tool

RESULTS_PER_SEARCH = 5
# Without a cap one search returns about 10,000 characters (about 2,700
# tokens). An analysis makes about 20 searches, so that would not fit the
# LLM's token limits. 1,000 characters per result still holds the answer.
CHARACTERS_PER_RESULT = 1000

MISSING_KEY_MESSAGE = (
    "EXA_API_KEY is not set. Add it to `.env`. "
    "You can create a free key at https://dashboard.exa.ai."
)


@register_tool
def web_search(query: str) -> str:
    """Search the public web for current information that is not in the
    company's documents: technical documentation, public prices of cloud
    services and vendors, competitors and their offerings, laws and
    regulations, and known incidents.

    Write the country into the query when it matters, for example
    "Paymob transaction fees Egypt". Returns the best matching pages, each
    with its URL and the passages that match the query, so you can cite the
    URL as evidence.
    """
    response = get_exa_client().search(
        query,
        type="auto",
        num_results=RESULTS_PER_SEARCH,
        # Highlights are the passages that match the query, chosen by Exa.
        # They make a better evidence snippet than the top of the page.
        contents={"highlights": {"max_characters": CHARACTERS_PER_RESULT}},
    )
    if not response.results:
        return "No matching web pages found."
    return "\n\n".join(_format_result(result) for result in response.results)


@lru_cache
def get_exa_client() -> Exa:
    # Created on the first search, so building the agents needs no API key.
    api_key = get_settings().exa_api_key
    if not api_key:
        raise RuntimeError(MISSING_KEY_MESSAGE)
    return Exa(api_key=api_key)


def _format_result(result: Result) -> str:
    published = f" (published {result.published_date[:10]})" if result.published_date else ""
    passages = "\n".join(result.highlights or [])
    return f"[source: {result.url}]\n{result.title or ''}{published}\n{passages}"
