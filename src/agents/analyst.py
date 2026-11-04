"""The shared work loop of the four analyst agents.

Technical, Financial, Competitor, and Risk all work the same way:

1. Read the idea, the supervisor's brief, their task, the other agents'
   findings, and the reviewer's feedback when their work was sent back.
2. Call their tools (company documents, web search) until they have what
   they need, at most `MAX_TOOL_ROUNDS` times.
3. Return one finding in the shape of their `output_type`.

The loop is written once here, so the four agents cannot drift apart. A
specialist changes its work through its prompt file, its task in
`config/tasks.yaml`, or its `output_type`. It overrides `analyze` only when
its work really differs.
"""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import BaseTool

from src.agents.base import BaseAgent
from src.agents.request import format_request, idea_sections
from src.memory import blackboard
from src.orchestrator.state import AgentFinding, FeasibilityState, FindingStatus
from src.utils.llm import structured_output
from src.utils.logger import get_logger

# How many times the LLM may ask for tools before it must answer. One round
# can hold several tool calls. 5 matches the search budget per agent in
# `docs/research/web_search_selection.md`.
MAX_TOOL_ROUNDS = 5

FINAL_ANSWER_REQUEST = (
    "Now write your finding. Cite every source you used as evidence, "
    "and list every assumption you made."
)

logger = get_logger(__name__)


class AnalystAgent(BaseAgent):
    def analyze(self, state: FeasibilityState) -> AgentFinding:
        messages = self._research([SystemMessage(self.system_prompt), HumanMessage(self._request(state))])
        finding = structured_output(self.llm, self.output_type).invoke(
            [*messages, HumanMessage(FINAL_ANSWER_REQUEST)]
        )
        # Who wrote the finding and whether it is done are facts, not the LLM's choice.
        return finding.model_copy(update={"agent": self.name, "status": FindingStatus.DONE})

    def _request(self, state: FeasibilityState) -> str:
        sections = idea_sections(state["idea"])
        sections["Your brief from the supervisor"] = blackboard.read_brief(state, self.name) or "No brief given."
        if self.task:
            sections["Your task"] = self.task.description
            sections["Expected output"] = self.task.expected_output
        others = {name: f for name, f in blackboard.read_findings(state).items() if name != self.name}
        if others:
            sections["Findings from the other agents"] = "\n".join(
                f"- {name} ({finding.status}): {finding.summary}" for name, finding in others.items()
            )
        feedback = self._reviewer_feedback(state)
        if feedback:
            sections["The reviewer sent your work back. Fix these issues"] = feedback
        return format_request(sections)

    def _reviewer_feedback(self, state: FeasibilityState) -> str | None:
        validation = blackboard.read_validation(state)
        if validation is None or self.name not in validation.revision_requests:
            return None
        return "\n".join(f"- {issue}" for issue in validation.issues) or validation.summary

    def _research(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """Let the LLM call tools until it stops asking or the round limit is reached."""
        if not self.tools:
            return messages
        model = self.llm.bind_tools(self.tools)
        tools_by_name = {tool.name: tool for tool in self.tools}
        for _ in range(MAX_TOOL_ROUNDS):
            reply: AIMessage = model.invoke(messages)
            messages = [*messages, reply]
            if not reply.tool_calls:
                break
            messages += [_call_tool(tools_by_name, call) for call in reply.tool_calls]
        return messages


def _call_tool(tools_by_name: dict[str, BaseTool], call: ToolCall) -> ToolMessage:
    """Run one tool call. A failure goes back to the LLM as text, so it can try another way."""
    tool = tools_by_name.get(call["name"])
    if tool is None:
        content = f"There is no tool named '{call['name']}'."
    else:
        try:
            content = tool.invoke(call["args"])
        except Exception as error:  # a tool that is down must not stop the analysis
            logger.warning("Tool %s failed: %s", call["name"], error)
            content = f"The tool failed: {error}"
    return ToolMessage(content, tool_call_id=call["id"])
