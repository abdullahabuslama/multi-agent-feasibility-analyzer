import pytest

from config.settings import load_agents_config
from src.agents import BaseAgent, build_agent
from src.orchestrator.state import AgentFinding, FindingStatus, TaskPlan
from src.utils.guardrails import GuardrailError
from tests.conftest import SAMPLE_IDEA

ANALYSTS = ["technical", "financial", "competitor", "risk"]


@pytest.mark.parametrize("name", list(load_agents_config()))
def test_every_configured_agent_builds(name: str) -> None:
    agent = build_agent(name)

    assert isinstance(agent, BaseAgent)
    assert agent.name == name
    assert agent.system_prompt.strip()


@pytest.mark.parametrize("name", ANALYSTS)
def test_stub_analyst_posts_pending_finding_under_its_name(name: str) -> None:
    update = build_agent(name).run({"idea": SAMPLE_IDEA})

    finding = update["findings"][name]
    assert finding.agent == name
    assert finding.status == FindingStatus.PENDING


def test_supervisor_posts_plan_with_only_known_agents() -> None:
    update = build_agent("supervisor").run({"idea": SAMPLE_IDEA})

    plan = update["plan"]
    assert isinstance(plan, TaskPlan)
    assert [brief.agent for brief in plan.briefs] == ["technical", "financial"]


def test_finding_signed_with_another_name_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = build_agent("technical")
    wrong = AgentFinding(agent="financial", status=FindingStatus.DONE, summary="x")
    monkeypatch.setattr(agent, "analyze", lambda _state: wrong)

    with pytest.raises(GuardrailError):
        agent.run({"idea": SAMPLE_IDEA})
