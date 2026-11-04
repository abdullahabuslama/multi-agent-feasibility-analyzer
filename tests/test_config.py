"""The config models catch broken YAML at load time."""

import pytest
from pydantic import ValidationError

from config.models import AgentConfig, WorkflowConfig
from config.settings import load_agents_config, load_tasks_config

REVIEW = {"agent": "validator", "max_revisions": 2}


def test_project_config_files_load() -> None:
    workflow = load_tasks_config().workflow

    assert set(workflow.agents) <= set(load_agents_config())
    assert workflow.stages[workflow.review_stage_index] == [workflow.review.agent]


def test_review_agent_must_be_alone_in_its_stage() -> None:
    with pytest.raises(ValidationError, match="alone in its stage"):
        WorkflowConfig(entry="supervisor", stages=[["technical", "validator"]], review=REVIEW)


def test_review_agent_must_be_in_a_stage() -> None:
    with pytest.raises(ValidationError, match="not in any workflow stage"):
        WorkflowConfig(entry="supervisor", stages=[["technical"]], review=REVIEW)


def test_agent_in_two_stages_is_rejected() -> None:
    with pytest.raises(ValidationError, match="more than one workflow stage"):
        WorkflowConfig(entry="supervisor", stages=[["technical"], ["technical"], ["validator"]], review=REVIEW)


def test_misspelled_agent_key_is_rejected() -> None:
    with pytest.raises(ValidationError, match="tool"):
        AgentConfig(class_path="x.Y", role="r", goal="g", prompt_file="p.md", tool=["web_search"])
