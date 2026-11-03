import logging
import re
from concurrent.futures import ThreadPoolExecutor

from agents import critic_chain, revision_chain, writer_chain
from tools import fetch_text, search_sources

logger = logging.getLogger(__name__)

MAX_SOURCES = 5
MAX_REVISIONS = 2
PASS_SCORE = 8.0


def _gather_sources(topic: str) -> list[dict]:
    """Search, then scrape every result in parallel. Falls back to the snippet when a page can't be read."""
    sources = search_sources(topic, max_results=MAX_SOURCES)

    def scrape(source: dict) -> dict:
        try:
            return {**source, "text": fetch_text(source["url"]), "scraped": True}
        except Exception as e:
            logger.warning("Could not scrape %s: %s", source["url"], e)
            return {**source, "text": source["snippet"], "scraped": False}

    if not sources:
        return []
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        return list(pool.map(scrape, sources))


def _format_search_results(sources: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet'][:300]}"
        for i, s in enumerate(sources, 1)
    )


def _format_research(sources: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {s['title']} ({s['url']})\n{s['text']}" for i, s in enumerate(sources, 1)
    )


def _format_source_list(sources: list[dict]) -> str:
    return "\n".join(f"[{i}] {s['title']} - {s['url']}" for i, s in enumerate(sources, 1))


def _parse_score(feedback: str) -> float | None:
    match = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    return float(match.group(1)) if match else None


def research_pipeline(topic: str) -> dict:
    sources = _gather_sources(topic)
    research = _format_research(sources) or "No sources were found."

    state = {
        "sources": [{"title": s["title"], "url": s["url"], "scraped": s["scraped"]} for s in sources],
        "search_results": _format_search_results(sources),
        "scraped_content": "\n\n".join(s["text"] for s in sources if s["scraped"]),
    }

    # The Sources list is appended by code, so the critic is shown it alongside the body.
    source_section = f"\n\n## Sources\n{_format_source_list(sources)}" if sources else ""

    report = writer_chain.invoke({"topic": topic, "research": research})
    feedback = critic_chain.invoke({"report": report.rstrip() + source_section})
    revisions = 0

    # Critic loop: revise until the score passes or the budget runs out.
    while revisions < MAX_REVISIONS:
        score = _parse_score(feedback)
        if score is None or score >= PASS_SCORE:
            break
        report = revision_chain.invoke(
            {"topic": topic, "research": research, "report": report, "feedback": feedback}
        )
        feedback = critic_chain.invoke({"report": report.rstrip() + source_section})
        revisions += 1

    state.update(report=report.rstrip() + source_section, feedback=feedback, score=_parse_score(feedback), revisions=revisions)
    return state


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = research_pipeline(input("Enter a research topic: "))
    print(result["report"])
    print("\n--- Critic ---\n", result["feedback"])
