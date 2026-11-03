import logging
from concurrent.futures import ThreadPoolExecutor

from agents import CriticReview, critic_chain, plan_topic, revision_chain, writer_chain
from tools import fetch_text, search_sources

logger = logging.getLogger(__name__)

MAX_SOURCES = 6
RESULTS_PER_QUESTION = 3
MAX_REVISIONS = 2
PASS_SCORE = 8.0


def _search_all(questions: list[str]) -> list[dict]:
    """Search every sub-question in parallel; interleave results, drop duplicate URLs, cap at MAX_SOURCES."""
    def search(question: str) -> list[dict]:
        try:
            return search_sources(question, max_results=RESULTS_PER_QUESTION)
        except Exception as e:
            logger.warning("Search failed for %r: %s", question, e)
            return []

    with ThreadPoolExecutor(max_workers=len(questions)) as pool:
        per_question = list(pool.map(search, questions))

    sources, seen = [], set()
    for rank in range(RESULTS_PER_QUESTION):
        for results in per_question:
            if rank < len(results) and results[rank]["url"] not in seen:
                seen.add(results[rank]["url"])
                sources.append(results[rank])
    return sources[:MAX_SOURCES]


def _gather_sources(questions: list[str]) -> list[dict]:
    """Search, then scrape every result in parallel. Falls back to the snippet when a page can't be read."""
    sources = _search_all(questions)

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


def _review(report: str) -> CriticReview | None:
    """Ask the critic for a structured review. A critic failure must not lose the finished report."""
    try:
        return critic_chain.invoke({"report": report})
    except Exception as e:
        logger.warning("Critic failed: %s", e)
        return None


def research_pipeline(topic: str) -> dict:
    questions = plan_topic(topic)
    sources = _gather_sources(questions)
    research = _format_research(sources) or "No sources were found."

    state = {
        "plan": questions,
        "sources": [{"title": s["title"], "url": s["url"], "scraped": s["scraped"]} for s in sources],
        "search_results": _format_search_results(sources),
        "scraped_content": "\n\n".join(s["text"] for s in sources if s["scraped"]),
    }

    # The Sources list is appended by code, so the critic is shown it alongside the body.
    source_section = f"\n\n## Sources\n{_format_source_list(sources)}" if sources else ""

    report = writer_chain.invoke({"topic": topic, "research": research})
    review = _review(report.rstrip() + source_section)
    revisions = 0

    # Critic loop: revise until the score passes or the budget runs out.
    while revisions < MAX_REVISIONS:
        if review is None or review.score >= PASS_SCORE:
            break
        report = revision_chain.invoke(
            {"topic": topic, "research": research, "report": report, "feedback": review.format()}
        )
        review = _review(report.rstrip() + source_section)
        revisions += 1

    state.update(
        report=report.rstrip() + source_section,
        feedback=review.format() if review else "Critic review unavailable.",
        score=review.score if review else None,
        revisions=revisions,
    )
    return state


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = research_pipeline(input("Enter a research topic: "))
    print(result["report"])
    print("\n--- Critic ---\n", result["feedback"])
