"""The shared analyst loop: tool calls, limits, and what goes into the request."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool, tool

from config.settings import load_agents_config
from src.agents.analyst import MAX_TOOL_ROUNDS
from src.agents.technical import TechnicalAgent
from src.orchestrator.state import AgentFinding, FindingStatus, ValidationResult
from tests.conftest import SAMPLE_IDEA, FakeChatModel

lookups: list[str] = []


@tool
def lookup_fees(query: str) -> str:
    """Test tool: returns a fixed fee fact."""
    lookups.append(query)
    return "Paymob charges 2.75% + EGP 3 per payment."


@tool
def broken_tool(query: str) -> str:
    """Test tool: always fails, like a service that is down."""
    raise ConnectionError("service unavailable")


def make_analyst(tools: list[BaseTool]) -> TechnicalAgent:
    # Built by hand, not from the YAML: the agent takes its prompt and tools as arguments.
    return TechnicalAgent(
        name="technical",
        config=load_agents_config()["technical"],
        system_prompt="You are a test analyst.",
        task=None,
        tools=tools,
    )


def ask_for(tool_name: str) -> AIMessage:
    return AIMessage("", tool_calls=[{"name": tool_name, "args": {"query": "fees"}, "id": "call-1"}])


def final_messages(fake_llm: FakeChatModel) -> list:
    """The messages the LLM saw when it wrote the finding."""
    return fake_llm.seen[-1]


def test_tool_result_reaches_the_llm_before_it_writes_the_finding(fake_llm: FakeChatModel) -> None:
    fake_llm.tool_replies = [ask_for("lookup_fees")]

    finding = make_analyst([lookup_fees]).analyze({"idea": SAMPLE_IDEA})

    tool_messages = [m for m in final_messages(fake_llm) if isinstance(m, ToolMessage)]
    assert [m.content for m in tool_messages] == ["Paymob charges 2.75% + EGP 3 per payment."]
    assert isinstance(finding, AgentFinding)
    assert (finding.agent, finding.status) == ("technical", FindingStatus.DONE)


def test_failing_tool_goes_back_to_the_llm_as_text(fake_llm: FakeChatModel) -> None:
    fake_llm.tool_replies = [ask_for("broken_tool")]

    make_analyst([broken_tool]).analyze({"idea": SAMPLE_IDEA})

    tool_message = next(m for m in final_messages(fake_llm) if isinstance(m, ToolMessage))
    assert tool_message.content.startswith("The tool failed: service unavailable")


def test_tool_rounds_stop_at_the_limit(fake_llm: FakeChatModel) -> None:
    lookups.clear()
    fake_llm.tool_replies = [ask_for("lookup_fees")] * (MAX_TOOL_ROUNDS + 3)

    make_analyst([lookup_fees]).analyze({"idea": SAMPLE_IDEA})

    assert len(lookups) == MAX_TOOL_ROUNDS


def test_request_includes_reviewer_feedback_when_work_was_sent_back(fake_llm: FakeChatModel) -> None:
    state = {
        "idea": SAMPLE_IDEA,
        "validation": ValidationResult(
            approved=False,
            summary="Missing evidence.",
            issues=["No source for the Orders API rate limit."],
            revision_requests=["technical"],
        ),
    }

    make_analyst([]).analyze(state)

    request = next(m for m in final_messages(fake_llm) if isinstance(m, HumanMessage)).content
    assert "No source for the Orders API rate limit." in request


def test_request_includes_other_agents_findings_but_not_its_own(fake_llm: FakeChatModel) -> None:
    state = {
        "idea": SAMPLE_IDEA,
        "findings": {
            "financial": AgentFinding(agent="financial", status=FindingStatus.DONE, summary="Payback in 14 months."),
            "technical": AgentFinding(agent="technical", status=FindingStatus.DONE, summary="My old finding."),
        },
    }

    make_analyst([]).analyze(state)

    request = next(m for m in final_messages(fake_llm) if isinstance(m, HumanMessage)).content
    assert "Payback in 14 months." in request
    assert "My old finding." not in request
