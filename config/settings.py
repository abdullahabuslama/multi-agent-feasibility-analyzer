"""App-wide settings and the loaders for the two YAML config files.

Values come from environment variables or the `.env` file in the project
root. Every other module asks this file for configuration, so there is one
place to look when a value seems wrong.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.models import AgentConfig, TasksConfig

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
PROMPTS_DIR = PROJECT_ROOT / "src" / "prompts"
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Typed view of the environment. Field names match `.env.example`."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    llm_provider: str = "groq"
    llm_model: str = "openai/gpt-oss-120b"

    exa_api_key: str = ""

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_path: Path = Path(".qdrant")
    qdrant_collection: str = "company_knowledge"

    knowledge_base_dir: Path = Path("data/knowledge_base")

    log_level: str = "INFO"

    @field_validator("qdrant_path", "knowledge_base_dir")
    @classmethod
    def _relative_to_project_root(cls, path: Path) -> Path:
        # Relative paths in `.env` mean "from the project root",
        # whatever folder the app is started from.
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    # Provider SDKs (Groq, OpenAI, ...) read their API key from the
    # environment themselves, so the `.env` values are also exported there.
    load_dotenv(ENV_FILE)
    return Settings()


@lru_cache
def load_agents_config() -> dict[str, AgentConfig]:
    """Agent definitions from `config/agents.yaml`, keyed by agent name."""
    return {name: AgentConfig(**entry) for name, entry in _read_yaml("agents.yaml").items()}


@lru_cache
def load_tasks_config() -> TasksConfig:
    """Workflow and task definitions from `config/tasks.yaml`.

    Also checks that every agent the workflow names is declared in
    `config/agents.yaml`, because the two files are edited separately.
    """
    config = TasksConfig(**_read_yaml("tasks.yaml"))
    workflow = config.workflow
    undeclared = sorted(set([workflow.entry, *workflow.agents]) - set(load_agents_config()))
    if undeclared:
        raise ValueError(f"tasks.yaml uses agents not declared in agents.yaml: {undeclared}.")
    return config


def _read_yaml(file_name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / file_name, encoding="utf-8") as file:
        return yaml.safe_load(file)
