# Building your agent

A guide for each team member who owns one agent. Read it once from top to
bottom, then use the steps for your agent type.

## LangGraph or LangChain? Both, for different jobs

**LangGraph runs the workflow. LangChain is what each agent uses inside.**
Think of a factory: LangGraph is the conveyor belt that moves the work from
station to station. LangChain is the set of tools each worker uses at their
station.

| Job | Library | Where in the code |
|---|---|---|
| The order of the agents, running in parallel, the revision loop | LangGraph `StateGraph` | `src/orchestrator/graph.py` |
| The shared state that moves between agents | LangGraph state | `src/orchestrator/state.py` |
| Deciding where to go after the validator | LangGraph conditional edge | `src/orchestrator/router.py` |
| Saving each run's state while the app runs | LangGraph checkpointer | `src/memory/short_term.py` |
| Creating the chat model (Groq) | LangChain `init_chat_model` | `src/utils/llm.py` |
| Messages, tool calls, structured output | LangChain core | `src/agents/analyst.py` |
| Tools the LLM can call | LangChain `@tool` | `src/tools/base.py` |
| Company documents search (RAG) | LangChain + Qdrant | `src/memory/long_term.py` |

**You will almost never touch LangGraph.** The graph is built from
`config/tasks.yaml`, so your agent becomes a step in the workflow just by
being listed there. All agents are already listed.

## Where the main code is

One analysis, from the HTTP request to the report:

```
POST /analyses                          api/app.py
  -> build_graph()                      src/orchestrator/graph.py   (built once)
       -> build_agent(name)             src/agents/base.py          (one per agent)
  -> graph.invoke({"idea": ...})
       supervisor.run(state)            src/agents/supervisor.py    writes a brief per agent
       technical / financial / competitor .run(state)   in parallel
       risk.run(state)
       validator.run(state)             can send work back (router.py)
       reporter.run(state)
```

Every `run(state)` does the same three things (`BaseAgent.run` in
`src/agents/base.py`):

1. Calls your `analyze(state)`.
2. Checks that you returned the right type (`src/utils/guardrails.py`).
3. Posts your result on the blackboard (`src/memory/blackboard.py`). The
   blackboard is the only code that writes the shared state.

**You write `analyze`. Everything around it already exists.**

## The files you own

| You own | Your files |
|---|---|
| Technical, Financial, Competitor, Risk | `src/agents/<name>.py`, `src/prompts/system_messages/<name>.md`, your entry in `config/agents.yaml` and `config/tasks.yaml` |
| Validator | `src/agents/validator.py`, `src/prompts/system_messages/validator.md`, its YAML entries |
| Reporter | `src/agents/reporter.py`, `src/prompts/system_messages/reporter.md`, its YAML entries |

## If you own an analyst (Technical, Financial, Competitor, Risk)

**Your agent already runs.** It uses the shared loop in
`src/agents/analyst.py`. On each run it:

1. Reads the idea, the supervisor's brief for you, your task, the other
   agents' findings, and the reviewer's feedback if your work was sent back.
2. Calls your tools (company documents, web search), at most 5 times.
3. Returns an `AgentFinding`: summary, score (0 to 10), assumptions, and
   evidence (source + snippet).

Make it yours in this order. Stop when the result is good enough. Most
agents need only steps 1 to 3.

### Step 1. Write your prompt

Edit `src/prompts/system_messages/<name>.md`. This is the biggest lever.
Say what to check, which tool to use for what, and what a good answer looks
like. You don't need to explain the idea or the brief. The loop adds those
to every request.

### Step 2. Sharpen your task

Edit your entry under `tasks:` in `config/tasks.yaml`. Your agent gets its
`description` and `expected_output`, and the supervisor also reads them
when it writes your brief.

### Step 3. Choose your tools

Edit the `tools:` list of your agent in `config/agents.yaml`. Today there
are `search_company_docs` (company documents) and `web_search` (Exa).

### Step 4. Add your own output fields

Need more than a summary, for example a cost table? Subclass
`AgentFinding` in your agent file and set `output_type`. The LLM is then
asked for your fields too. The blackboard, the API, and the validator
handle the subclass without any change.

```python
# src/agents/financial.py
from pydantic import BaseModel, Field

from src.agents.analyst import AnalystAgent
from src.orchestrator.state import AgentFinding


class CostItem(BaseModel):
    item: str
    one_time_egp: float = 0
    monthly_egp: float = 0


class FinancialFinding(AgentFinding):
    costs: list[CostItem] = Field(default_factory=list)
    monthly_benefit_egp: float | None = None
    payback_months: float | None = None


class FinancialAgent(AnalystAgent):
    output_type = FinancialFinding
```

Write a `description=` on each `Field` when its meaning is not obvious. The
LLM reads it.

### Step 5. Only if you must: change how the agent works

Override `analyze` only when the shared loop is not enough. A common case:
**the Financial agent must not let the LLM do arithmetic.** Let the loop get
the numbers, then compute in Python:

```python
class FinancialAgent(AnalystAgent):
    output_type = FinancialFinding

    def analyze(self, state: FeasibilityState) -> FinancialFinding:
        finding = super().analyze(state)
        return finding.model_copy(update={"payback_months": payback_months(finding)})


def payback_months(finding: FinancialFinding) -> float | None:
    one_time = sum(cost.one_time_egp for cost in finding.costs)
    monthly_cost = sum(cost.monthly_egp for cost in finding.costs)
    net_monthly = (finding.monthly_benefit_egp or 0) - monthly_cost
    return round(one_time / net_monthly, 1) if net_monthly > 0 else None
```

## If you own the Validator

Your agent returns a `ValidationResult`: `approved`, `summary`, `issues`,
and `revision_requests`. **The names in `revision_requests` decide which
agents run again.** Use the exact agent names (`technical`, `risk`, ...).
The router sends the work back at most `max_revisions` times
(`config/tasks.yaml`). Each named agent sees your `issues` in its next
request.

A starting point for `src/agents/validator.py`:

```python
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import BaseAgent
from src.agents.request import format_request, idea_sections
from src.memory import blackboard
from src.orchestrator.state import FeasibilityState, ValidationResult
from src.utils.llm import structured_output


class ValidatorAgent(BaseAgent):
    output_type = ValidationResult

    def analyze(self, state: FeasibilityState) -> ValidationResult:
        sections = idea_sections(state["idea"])
        sections["Findings to check"] = "\n\n".join(
            finding.model_dump_json(indent=2) for finding in blackboard.read_findings(state).values()
        )
        return structured_output(self.llm, ValidationResult).invoke(
            [SystemMessage(self.system_prompt), HumanMessage(format_request(sections))]
        )
```

## If you own the Reporter

Your agent returns a `FinalReport` with one field, `markdown`. Read what
you need from the blackboard: `blackboard.read_findings(state)` and
`blackboard.read_validation(state)`. Use the same pattern as the validator
example above, with `FinalReport` as the output model.

## Adding a tool

A tool does one action. The agent decides when to use it.

1. Create a file in `src/tools/`, or add to an existing one:

   ```python
   from src.tools.base import register_tool


   @register_tool
   def currency_to_egp(amount: float, currency: str) -> str:
       """Convert an amount to Egyptian pounds at today's rate.

       Use it before comparing prices quoted in other currencies.
       """
       ...
   ```

   **The docstring is what the LLM reads** to decide when to call the
   tool, so write it for the LLM.
2. If it is a new file, import it in `src/tools/__init__.py` (one line).
3. Add the tool name to `tools:` of the agents that need it in
   `config/agents.yaml`.

## Testing your agent

Tests use a fake LLM (`tests/conftest.py`), so they need no API key and no
internet. Put your tests in `tests/test_agents/`.

```python
from src.agents import build_agent
from src.agents.financial import CostItem, FinancialFinding
from src.orchestrator.state import FindingStatus
from tests.conftest import SAMPLE_IDEA


def test_payback_is_computed_in_python(fake_llm) -> None:
    fake_llm.answers[FinancialFinding] = FinancialFinding(
        agent="financial",
        status=FindingStatus.DONE,
        summary="Pilot pays back.",
        costs=[CostItem(item="Integration", one_time_egp=120_000, monthly_egp=5_000)],
        monthly_benefit_egp=15_000,
    )

    update = build_agent("financial").run({"idea": SAMPLE_IDEA})

    assert update["findings"]["financial"].payback_months == 12.0
```

- `fake_llm.answers[YourModel] = ...` sets what the "LLM" returns.
- `fake_llm.tool_replies = [...]` makes it call tools first. See
  `tests/test_agents/test_analyst.py` for examples.
- Run everything with `pytest`.

To try your agent for real (needs `GROQ_API_KEY` and `EXA_API_KEY` in
`.env`):

```bash
python -c "
from src.agents import build_agent
from src.orchestrator.state import BusinessIdea
idea = BusinessIdea(idea='Offer buy now, pay later at checkout for orders above EGP 3,000.')
print(build_agent('competitor').analyze({'idea': idea}).model_dump_json(indent=2))
"
```

## Rules that keep the agents working together

- **Return your output model. Never write the state yourself.** The
  blackboard does that.
- **Don't read config files or prompt files in your agent.** `build_agent`
  gives you `self.config`, `self.system_prompt`, `self.task`, and
  `self.tools`.
- **Use `structured_output(self.llm, Model)`** from `src/utils/llm.py`, not
  `with_structured_output` directly. It holds a provider setting that
  stops the model answering in plain text.
- **Keep what you send to the LLM small.** Groq's free tier allows 8,000
  tokens per minute for all agents together. Long prompts or large tool
  results make runs slow, or make them fail.
- **Cite sources.** Put each URL or file name in `evidence`. The validator
  checks claims against it.
