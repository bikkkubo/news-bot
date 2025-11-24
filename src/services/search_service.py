import logging
from typing import List, Dict, Any
from duckduckgo_search import DDGS
import time
import random

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.ddgs = DDGS()

    def search_news_context(self, query: str, ticker: str = None, max_results: int = 5) -> str:
        """
        Search for additional context using DuckDuckGo.
        Returns a combined string of snippets.
        """
        try:
            # Construct high-precision query
            # Add (Bloomberg OR Reuters OR "Wall Street Journal") to prioritize high-quality syndicated content
            sources_hint = '(Bloomberg OR Reuters OR "Wall Street Journal")'
            
            if ticker:
                search_query = f"${ticker} stock price reaction {query} {sources_hint}"
            else:
                search_query = f"{query} latest update stock price {sources_hint}"
            
            logger.info(f"Searching web for: {search_query}")
            
            results = self.ddgs.text(search_query, max_results=max_results)
            
            if not results:
                return "No additional context found via web search."

            context_parts = []
            for r in results:
                title = r.get('title', 'No Title')
                snippet = r.get('body', '')
                link = r.get('href', '')
                context_parts.append(f"Source: {title} ({link})\nSummary: {snippet}")
            
            combined_context = "\n\n".join(context_parts)
            return combined_context

        except Exception as e:
            logger.error(f"Web search failed for '{query}': {e}")
            return f"Search failed: {e}"

    def enrich_article(self, article: Dict[str, Any], ticker: str = None) -> Dict[str, Any]:
        """
        Add search context to an article dictionary.
        """
        # Sleep briefly to avoid rate limits if calling in a loop
        time.sleep(random.uniform(1.0, 2.0))
        
        title = article.get('title', '')
        if title:
            context = self.search_news_context(title, ticker=ticker)
            article['search_context'] = context
        else:
            article['search_context'] = "No title to search."
            
        return article
