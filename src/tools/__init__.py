"""Tools agents can call.

Importing a tool module registers its tools, so every module with tools is
imported here. A new tool file = one new import line below.
"""

from src.tools import db_tool, web_search  # noqa: F401  (imported to register their tools)
from src.tools.base import TOOL_REGISTRY, register_tool, resolve_tools

__all__ = ["TOOL_REGISTRY", "register_tool", "resolve_tools"]
