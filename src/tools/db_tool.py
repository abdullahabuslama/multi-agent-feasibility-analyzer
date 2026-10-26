"""Tools that query the company knowledge base (the RAG layer)."""

from src.memory.long_term import get_retriever
from src.tools.base import register_tool

RESULTS_PER_SEARCH = 4


@register_tool
def search_company_docs(query: str) -> str:
    """Search the company's internal documents: company profile, products,
    departments and processes, IT architecture, APIs, security and data
    policies, financial assumptions, and past projects.

    Use it for facts about this company. Returns the best matching passages,
    each with its source file name, so you can cite it as evidence.
    """
    documents = get_retriever(k=RESULTS_PER_SEARCH).invoke(query)
    if not documents:
        return "No matching company documents found."
    return "\n\n".join(
        f"[source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in documents
    )
