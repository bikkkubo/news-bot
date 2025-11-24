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

        # Filter articles based on keywords and time
        # Filter articles based on keywords and time
        from src.config import EXCLUDED_KEYWORDS, NON_US_KEYWORDS
        from datetime import datetime, timedelta, timezone
        import dateutil.parser

        # 12-hour window check (Temporarily set to 48h for testing as sample data is old)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=48)
        
        filtered_articles = []
        for article in all_articles:
            title = article['title'].lower()
            description = (article['description'] or "").lower()
            
            # 1. Time Check
            try:
                pub_date = dateutil.parser.parse(article['publishedAt'])
                if pub_date < cutoff_time:
                    logger.info(f"Skipping old article: {article['title']} ({article['publishedAt']})")
                    continue
            except Exception as e:
                logger.warning(f"Date parsing failed for {article['title']}: {e}")
                # If date parsing fails, we might skip or keep. Let's keep to be safe but log it.
                pass

            # 2. Lifestyle/Irrelevant Check
            if any(keyword in title for keyword in EXCLUDED_KEYWORDS):
                logger.info(f"Skipping lifestyle/irrelevant article: {article['title']}")
                continue

            # 3. Non-US/UK Check
            # If title contains UK keywords, check if it ALSO contains US keywords.
            # If ONLY UK keywords are present, skip it.
            us_safe_keywords = ["us", "u.s.", "american", "wall street", "fed ", "federal reserve", "dollar", "nasdaq", "nyse", "dow"]
            
            has_non_us = any(k in title for k in NON_US_KEYWORDS)
            has_us_safe = any(k in title for k in us_safe_keywords)
            
            if has_non_us and not has_us_safe:
                logger.info(f"Skipping non-US (UK/EU) article: {article['title']}")
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

        # --- Web Search Enrichment ---
        # Only enrich the top N articles to save time/bandwidth
        # Since we filter heavily, we might have fewer articles, but let's limit to be safe.
        from src.services.search_service import SearchService
        search_service = SearchService()
        
        enriched_articles = []
        # Limit enrichment to top 15 to match report generation limit
        for i, article in enumerate(unique_articles):
            if i < 15:
                logger.info(f"Enriching article {i+1}/{len(unique_articles)}: {article['title']}")
                enriched_article = search_service.enrich_article(article)
                enriched_articles.append(enriched_article)
            else:
                enriched_articles.append(article)

        return enriched_articles

if __name__ == "__main__":
    # Simple test
    try:
        collector = NewsDataCollector()
        news = collector.fetch_news()
        for item in news:
            print(f"- {item['title']} ({item['source']})")
    except Exception as e:
        print(f"Test failed: {e}")
