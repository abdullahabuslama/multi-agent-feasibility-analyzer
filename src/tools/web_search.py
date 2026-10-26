"""Web search tool — not built yet.

Choosing the search service is an open team task. Until it is decided,
this file stays empty and no `web_search` tool is registered.

What the agents will need from it:
- The Technical agent: current technical capabilities and documentation.
- The Financial agent: public prices of cloud services, APIs, and vendors.
- The Competitor agent: competitors, their offerings, pricing, and positioning.
- The Risk agent: regulations, known limitations, and incidents.
- Every result must keep its URL, so findings can cite it as `Evidence`.

When it is built: write the function with `@register_tool` from
`src/tools/base.py`, import this module in `src/tools/__init__.py`, and add
the tool name to the agents that need it in `config/agents.yaml`.
"""
