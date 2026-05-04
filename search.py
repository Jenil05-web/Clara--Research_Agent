"""
tools/search.py
───────────────
All web and academic search tools:
  - Wikipedia  (via LangChain community wrapper)
  - arXiv      (via LangChain community wrapper)
  - Exa        (via exa-py SDK  →  pip install exa-py)
"""

from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_core.tools import tool
from config import EXA_API_KEY


def build_search_tools() -> list:
    tools = []

    # ── Wikipedia ─────────────────────────────────────────────
    wiki = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=800)
    )
    wiki.name        = "wikipedia_search"
    wiki.description = (
        "Search Wikipedia for general knowledge, facts, history, or people. "
        "Use for broad informational questions that don't need real-time data."
    )
    tools.append(wiki)

    # ── arXiv ─────────────────────────────────────────────────
    arxiv = ArxivQueryRun(
        api_wrapper=ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=800)
    )
    arxiv.name        = "arxiv_search"
    arxiv.description = (
        "Search arXiv for academic papers on ML/AI, science, or research topics. "
        "Use when the user asks about research, papers, or technical studies."
    )
    tools.append(arxiv)

    # ── Exa (real-time web) ───────────────────────────────────
    if EXA_API_KEY:
        try:
            from exa_py import Exa
            exa = Exa(api_key=EXA_API_KEY)

            @tool
            def exa_web_search(query: str, num_results: int = 5) -> str:
                """
                Search the web in real-time using Exa.
                Use for current events, news, or any live information
                not available in Wikipedia or arXiv.
                """
                try:
                    results = exa.search_and_contents(
                        query, num_results=num_results,
                        text={"max_characters": 1000},
                    )
                    if not results.results:
                        return "No results found."
                    out = []
                    for r in results.results:
                        snippet = (r.text or "")[:500].strip()
                        out.append(f"**{r.title}**\n{r.url}\n{snippet}")
                    return "\n\n---\n\n".join(out)
                except Exception as e:
                    return f"Exa search error: {e}"

            @tool
            def exa_find_similar(url: str, num_results: int = 5) -> str:
                """Find web pages similar to a given URL using Exa."""
                try:
                    results = exa.find_similar_and_contents(
                        url, num_results=num_results,
                        text={"max_characters": 500},
                    )
                    if not results.results:
                        return "No similar pages found."
                    return "\n\n".join(
                        f"**{r.title}**\n{r.url}" for r in results.results
                    )
                except Exception as e:
                    return f"Exa find-similar error: {e}"

            @tool
            def exa_get_contents(url: str) -> str:
                """Fetch and return the full text content of a specific URL using Exa."""
                try:
                    results = exa.get_contents([url], text={"max_characters": 3000})
                    if not results.results:
                        return "Could not fetch content."
                    r = results.results[0]
                    return f"**{r.title}**\n{r.url}\n\n{r.text or 'No text extracted.'}"
                except Exception as e:
                    return f"Exa get-contents error: {e}"

            tools.extend([exa_web_search, exa_find_similar, exa_get_contents])

        except ImportError:
            print("⚠️  exa-py not installed. Run: pip install exa-py")

    return tools