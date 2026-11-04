"""How agents write the request message they send to the LLM.

The request is a list of titled sections ("Business idea", "Your brief",
...). Every agent describes the idea with the same sections, so the LLM
sees the idea the same way at every step.
"""

from src.orchestrator.state import BusinessIdea


def idea_sections(idea: BusinessIdea) -> dict[str, str]:
    return {
        "Business idea": idea.idea,
        "Extra context from the user": idea.context or "None given.",
    }


def format_request(sections: dict[str, str]) -> str:
    return "\n\n".join(f"{title}:\n{text.strip()}" for title, text in sections.items())
