"""The one place that creates chat models and asks them for structured output.

The provider and model come from `.env` (`LLM_PROVIDER`, `LLM_MODEL`).
An agent can override them, or the temperature, in its `llm:` block in
`config/agents.yaml`. Moving from Groq to another provider is a `.env`
change plus installing that provider's LangChain package.
"""

from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from config.settings import get_settings


def get_chat_model(llm_params: dict[str, Any] | None = None) -> BaseChatModel:
    settings = get_settings()
    params = dict(llm_params or {})
    model = params.pop("model", settings.llm_model)
    provider = params.pop("provider", settings.llm_provider)
    return init_chat_model(model, model_provider=provider, **params)


# "json_schema" makes the provider return JSON that matches the model, and
# nothing else. The default way ("function_calling") lets the model answer
# in plain text instead: Groq's gpt-oss did exactly that after a long
# research step, and the call failed. If a new provider does not support
# "json_schema", change it here.
STRUCTURED_OUTPUT_METHOD = "json_schema"


def structured_output(llm: BaseChatModel, schema: type[BaseModel]) -> Runnable:
    """`llm`, set up to answer with an instance of `schema`."""
    return llm.with_structured_output(schema, method=STRUCTURED_OUTPUT_METHOD)
