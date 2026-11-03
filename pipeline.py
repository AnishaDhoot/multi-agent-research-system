import logging
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from agents import CriticReview, critic_chain, plan_topic, revision_chain, writer_chain
from settings import MAX_REVISIONS, MAX_SOURCES, PASS_SCORE, RESULTS_PER_QUESTION
from tools import fetch_text_robust, search_sources

logger = logging.getLogger(__name__)

_TRUSTED_HOSTS = (
    "nature.com", "science.org", "sciencedirect.com", "mdpi.com", "ieee.org", "arxiv.org",
    "springer.com", "nih.gov", "who.int", "reuters.com", "bbc.com", "apnews.com",
)
_LOW_TRUST_HOSTS = ("medium.com", "quora.com", "reddit.com", "pinterest.com", "blogspot.com")
_CITATION = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]")


def _trust(url: str) -> int:
    """Rough source-quality score from the domain; used only to order search results."""
    host = (urlparse(url).hostname or "").lower()
    if host.endswith(_LOW_TRUST_HOSTS):
        return -1
    if host.endswith((".gov", ".edu")) or ".ac." in host or host.endswith(_TRUSTED_HOSTS):
        return 2
    return 1 if host.endswith(".org") else 0


def _search_all(questions: list[str]) -> list[dict]:
    """Search every sub-question in parallel; interleave results, drop duplicate URLs, cap at MAX_SOURCES."""
    def search(question: str) -> list[dict]:
        try:
            results = search_sources(question, max_results=RESULTS_PER_QUESTION)
        except Exception as e:
            logger.warning("Search failed for %r: %s", question, e)
            return []
        return sorted(results, key=lambda r: -_trust(r["url"]))  # stable: keeps Tavily's order on ties

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
            return {**source, "text": fetch_text_robust(source["url"]), "scraped": True}
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


def _cited_numbers(report: str) -> set[int]:
    return {int(n) for group in _CITATION.findall(report) for n in re.split(r"[,;]", group)}


def _renumber(report: str, mapping: dict[int, int]) -> str:
    """Rewrite inline [n] citations using mapping (old -> new); numbers not in the mapping are dropped."""
    def replace(match: re.Match) -> str:
        new = [mapping[int(n)] for n in re.split(r"[,;]", match.group(1)) if int(n) in mapping]
        return f"[{', '.join(map(str, new))}]" if new else ""

    return _CITATION.sub(replace, report)


def _review(report: str) -> CriticReview | None:
    """Ask the critic for a structured review. A critic failure must not lose the finished report."""
    try:
        return critic_chain.invoke({"report": report})
    except Exception as e:
        logger.warning("Critic failed: %s", e)
        return None


def research_pipeline(topic: str, on_progress=None) -> dict:
    def progress(stage: str) -> None:
        if on_progress:
            on_progress(stage)

    progress("planning")
    questions = plan_topic(topic)
    progress("reading sources")
    sources = _gather_sources(questions)
    research = _format_research(sources) or "No sources were found."

    state = {
        "plan": questions,
        "sources": [{"title": s["title"], "url": s["url"], "scraped": s["scraped"]} for s in sources],
        "search_results": _format_search_results(sources),
        "scraped_content": "\n\n".join(s["text"] for s in sources if s["scraped"]),
    }

    # The critic is shown the Sources list too, since code appends it to the final report.
    source_section = f"\n\n## Sources\n{_format_source_list(sources)}" if sources else ""

    progress("writing")
    report = writer_chain.invoke({"topic": topic, "research": research})
    progress("reviewing")
    review = _review(report.rstrip() + source_section)
    revisions = 0

    # Critic loop: revise until the score passes or the budget runs out.
    while revisions < MAX_REVISIONS:
        if review is None or review.score >= PASS_SCORE:
            break
        progress("revising")
        report = revision_chain.invoke(
            {"topic": topic, "research": research, "report": report, "feedback": review.format()}
        )
        review = _review(report.rstrip() + source_section)
        revisions += 1

    # List only sources the report actually cites, renumbered to stay contiguous.
    cited = sorted(_cited_numbers(report) & set(range(1, len(sources) + 1)))
    if cited and len(cited) < len(sources):
        report = _renumber(report, {old: new for new, old in enumerate(cited, 1)})
        sources = [sources[n - 1] for n in cited]
    final_sources = f"\n\n## Sources\n{_format_source_list(sources)}" if sources else ""

    state.update(
        report=report.rstrip() + final_sources,
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
