"""The tool registry: how tools are declared and how agents get them.

A tool is a normal Python function with a docstring, marked with
`@register_tool`. Agents ask for tools by name in `config/agents.yaml`;
`resolve_tools` turns those names into LangChain tools. A name that does not
exist fails when the agent is built, not in the middle of a run.
"""

from collections.abc import Callable
from typing import Any

from langchain_core.tools import BaseTool, tool

TOOL_REGISTRY: dict[str, BaseTool] = {}


def register_tool(func: Callable[..., Any]) -> BaseTool:
    """Turn `func` into a LangChain tool and add it to the registry.

    The function name becomes the tool name, and the docstring is what the
    LLM reads to decide when to call it, so write it for the LLM.
    """
    new_tool = tool(func)
    if new_tool.name in TOOL_REGISTRY:
        raise ValueError(f"A tool named '{new_tool.name}' is already registered.")
    TOOL_REGISTRY[new_tool.name] = new_tool
    return new_tool


def resolve_tools(names: list[str]) -> list[BaseTool]:
    unknown = [name for name in names if name not in TOOL_REGISTRY]
    if unknown:
        raise KeyError(f"Unknown tools {unknown}. Registered tools: {sorted(TOOL_REGISTRY)}.")
    return [TOOL_REGISTRY[name] for name in names]
