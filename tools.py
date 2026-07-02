# from langchain.tools import tool
# import requests
# from bs4 import BeautifulSoup
# from tavily import TavilyClient
# import os
# from dotenv import load_dotenv
# from rich import print
# load_dotenv()



# tavily= TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# @tool
# def web_search(query: str)->str:
#     """Search the web for recent and reliable information on a topic. Returns titles, URLs and snippets."""
#     results= tavily.search(query=query,max_results=5)
    
#     out=[]

#     for r in results['results']:
#         out.append(f'Title: {r["title"]}\nURL: {r["url"]}\nSnippet: {r["content"][:300]}\n\n')

#     return "\n-------\n".join(out)

# # print(web_search.invoke("langchain"))
 
# @tool
# @tool
# def scrape_url(url: str) -> str:
#     """Scrape and return clean text content from a given URL for a deeper reading."""
#     try:
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#             "Accept-Language": "en-US,en;q=0.5",
#             "Connection": "keep-alive",
#         }
#         response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.content, 'html.parser')
#         for tag in soup(['script', 'style', 'nav', 'footer']):
#             tag.decompose()
#         text = soup.get_text(separator=' ', strip=True)[:3000]
#         return text if text.strip() else "Page loaded but no readable content found."
#     except Exception as e:
#         return f"Could not scrape URL (skipping): {str(e)}"

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic."""
    results = tavily.search(query=query, max_results=5)
    out = []
    for r in results['results']:
        out.append(f'Title: {r["title"]}\nURL: {r["url"]}\nSnippet: {r["content"][:300]}\n\n')
    return "\n-------\n".join(out)

@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        text = soup.get_text(separator=' ', strip=True)[:3000]
        return text if text.strip() else "Page loaded but no readable content found."
    except Exception as e:
        return f"Could not scrape URL (skipping): {str(e)}"