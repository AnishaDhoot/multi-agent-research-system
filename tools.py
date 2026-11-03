import ipaddress
import os
import socket
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.tools import tool
import trafilatura
from tavily import TavilyClient

from settings import MAX_SCRAPE_CHARS

load_dotenv()

MAX_REDIRECTS = 3
SEARCH_ATTEMPTS = 3
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_tavily = None


def _get_tavily() -> TavilyClient:
    # Built lazily so importing this module doesn't require TAVILY_API_KEY.
    global _tavily
    if _tavily is None:
        _tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _tavily


def search_sources(query: str, max_results: int = 5) -> list[dict]:
    """Search the web and return [{title, url, snippet}, ...]."""
    for attempt in range(SEARCH_ATTEMPTS):
        try:
            results = _get_tavily().search(query=query, max_results=max_results)
            break
        except Exception:
            if attempt == SEARCH_ATTEMPTS - 1:
                raise
            time.sleep(2**attempt)
    return [
        {"title": r.get("title", ""), "url": r["url"], "snippet": r.get("content", "")}
        for r in results.get("results", [])
    ]


def is_safe_url(url: str) -> bool:
    """Only allow http(s) URLs that resolve exclusively to public IP addresses (SSRF guard)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror:
        return False
    return all(ipaddress.ip_address(info[4][0]).is_global for info in infos)


def _extract_main_text(response: requests.Response) -> str:
    """Main article text via trafilatura; falls back to plain tag-stripping for odd pages."""
    text = trafilatura.extract(response.text, include_comments=False, include_tables=False)
    if text:
        return text
    soup = BeautifulSoup(response.content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def fetch_text(url: str, limit: int = MAX_SCRAPE_CHARS) -> str:
    """Fetch a page and return its readable text. Raises on failure or unsafe URLs."""
    for _ in range(MAX_REDIRECTS + 1):
        if not is_safe_url(url):
            raise ValueError(f"Blocked or invalid URL: {url}")
        # Redirects are followed by hand so every hop is checked.
        response = requests.get(url, timeout=15, headers=HEADERS, allow_redirects=False)
        if response.is_redirect:
            url = urljoin(url, response.headers.get("Location", ""))
            continue
        response.raise_for_status()
        text = _extract_main_text(response)[:limit]
        if not text.strip():
            raise ValueError("Page loaded but no readable content found.")
        return text
    raise ValueError("Too many redirects")


def extract_via_tavily(url: str, limit: int = MAX_SCRAPE_CHARS) -> str:
    """Ask Tavily to fetch the page. Works on many sites that block our own scraper."""
    if not is_safe_url(url):
        raise ValueError(f"Blocked or invalid URL: {url}")
    result = _get_tavily().extract(urls=[url], extract_depth="advanced")
    items = result.get("results") or []
    text = (items[0].get("raw_content") or "")[:limit] if items else ""
    if not text.strip():
        raise ValueError("Tavily returned no content")
    return text


def fetch_text_robust(url: str, limit: int = MAX_SCRAPE_CHARS) -> str:
    """Direct fetch first; Tavily Extract as a fallback. Raises the direct-fetch error if both fail."""
    try:
        return fetch_text(url, limit)
    except Exception as direct_error:
        try:
            return extract_via_tavily(url, limit)
        except Exception:
            raise direct_error


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic."""
    return "\n-------\n".join(
        f'Title: {s["title"]}\nURL: {s["url"]}\nSnippet: {s["snippet"][:300]}\n\n'
        for s in search_sources(query)
    )


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL."""
    try:
        return fetch_text_robust(url)
    except Exception as e:
        return f"Could not scrape URL (skipping): {e}"
