"""The one place that creates chat models.

The provider and model come from `.env` (`LLM_PROVIDER`, `LLM_MODEL`).
An agent can override them, or the temperature, in its `llm:` block in
`config/agents.yaml`. Moving from Groq to another provider is a `.env`
change plus installing that provider's LangChain package.
"""

from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from config.settings import get_settings


def get_chat_model(llm_params: dict[str, Any] | None = None) -> BaseChatModel:
    settings = get_settings()
    params = dict(llm_params or {})
    model = params.pop("model", settings.llm_model)
    provider = params.pop("provider", settings.llm_provider)
    return init_chat_model(model, model_provider=provider, **params)
