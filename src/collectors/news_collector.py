from newsapi import NewsApiClient
import logging
from typing import List, Dict, Any
from src.config import NEWSAPI_KEY, ALLOWED_NEWS_SOURCES

logger = logging.getLogger(__name__)

class NewsDataCollector:
    def __init__(self):
        if not NEWSAPI_KEY:
            raise ValueError("NEWSAPI_KEY is not set in environment variables.")
        self.newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
        self.sources_str = ",".join(ALLOWED_NEWS_SOURCES)

    def fetch_news(self) -> List[Dict[str, Any]]:
        """
        Fetch top headlines from allowed sources (Reuters, Bloomberg, WSJ).
        Returns a list of news articles.
        """
        all_articles = []
        
        try:
            # Fetch top headlines
            # Note: 'country' cannot be mixed with 'sources' in NewsAPI
            response = self.newsapi.get_top_headlines(
                sources=self.sources_str,
                page_size=30  # Fetch enough to filter down to 15
            )
            
            if response['status'] == 'ok':
                articles = response['articles']
                logger.info(f"Fetched {len(articles)} articles from NewsAPI.")
                
                for article in articles:
                    # Basic validation
                    if article['title'] and article['url']:
                        # Ensure source is strictly allowed (double check)
                        source_id = article['source']['id']
                        if source_id in ALLOWED_NEWS_SOURCES:
                            all_articles.append({
                                "title": article['title'],
                                "url": article['url'],
                                "publishedAt": article['publishedAt'],
                                "source": article['source']['name'],
                                "description": article['description'],
                                "content": article['content']
                            })
                        else:
                            logger.warning(f"Filtered out article from unauthorized source: {source_id}")
            else:
                logger.error(f"NewsAPI returned error status: {response.get('code')} - {response.get('message')}")

        except Exception as e:
            logger.error(f"Error fetching news from NewsAPI: {e}")

        # Filter articles based on keywords
        from src.config import EXCLUDED_KEYWORDS
        
        filtered_articles = []
        for article in all_articles:
            title = article['title'].lower()
            description = (article['description'] or "").lower()
            
            # Check for excluded keywords
            if any(keyword in title for keyword in EXCLUDED_KEYWORDS):
                logger.info(f"Skipping lifestyle/irrelevant article: {article['title']}")
                continue
                
            filtered_articles.append(article)

        # Deduplication logic (simple title check)
        unique_articles = []
        seen_titles = set()
        
        for article in filtered_articles:
            title = article['title']
            if title not in seen_titles:
                unique_articles.append(article)
                seen_titles.add(title)
            else:
                logger.info(f"Duplicate article skipped: {title}")

        return unique_articles

if __name__ == "__main__":
    # Simple test
    try:
        collector = NewsDataCollector()
        news = collector.fetch_news()
        for item in news:
            print(f"- {item['title']} ({item['source']})")
    except Exception as e:
        print(f"Test failed: {e}")
