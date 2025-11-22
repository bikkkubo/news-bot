import unittest
from unittest.mock import MagicMock, patch
import os

# Mock environment variables before importing modules that might use them at top level
with patch.dict(os.environ, {'NEWSAPI_KEY': 'test_key'}):
    from src.collectors.news_collector import NewsDataCollector
    from src.collectors.stock_collector import StockDataCollector
    from src.services.llm_service import LLMService
    from src.config import MARKET_NAMES

class TestCollectors(unittest.TestCase):
    
    @patch('src.collectors.news_collector.NewsApiClient')
    @patch('src.collectors.news_collector.NEWSAPI_KEY', 'test_key')
    def test_news_collector_filtering(self, mock_newsapi_cls):
        # Setup mock
        mock_client = MagicMock()
        mock_newsapi_cls.return_value = mock_client
        
        mock_response = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'Valid News',
                    'url': 'http://reuters.com/news',
                    'publishedAt': '2025-11-22T10:00:00Z',
                    'source': {'id': 'reuters', 'name': 'Reuters'},
                    'description': 'Test',
                    'content': 'Test'
                },
                {
                    'title': 'Invalid News',
                    'url': 'http://investing.com/news',
                    'publishedAt': '2025-11-22T10:00:00Z',
                    'source': {'id': 'investing-com', 'name': 'Investing.com'},
                    'description': 'Test',
                    'content': 'Test'
                }
            ]
        }
        mock_client.get_top_headlines.return_value = mock_response
        
        # Test
        collector = NewsDataCollector()
        news = collector.fetch_news()
        
        # Assert
        self.assertEqual(len(news), 1)
        self.assertEqual(news[0]['title'], 'Valid News')
        self.assertEqual(news[0]['source'], 'Reuters')

    @patch('src.collectors.stock_collector.yf.Ticker')
    def test_stock_collector_naming(self, mock_ticker_cls):
        # Setup mock
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        
        # Mock history
        mock_hist = MagicMock()
        mock_hist.__len__.return_value = 2
        mock_hist.__getitem__.return_value.iloc.__getitem__.side_effect = [100.0, 110.0] # prev, current
        
        collector = StockDataCollector()
        # Check if keys map to correct Japanese names
        self.assertIn("ナスダック総合指数", [MARKET_NAMES[k] for k in collector.tickers.keys()])

class TestLLMService(unittest.TestCase):
    def test_prompt_structure(self):
        # Verify system prompts contain key constraints
        fact_prompt = LLMService.get_fact_extraction_system_prompt()
        self.assertIn("FACTS ONLY", fact_prompt)
        self.assertIn("NO OPINIONS", fact_prompt)
        self.assertIn("([Source Name](URL))", fact_prompt)
        
        persona_prompt = LLMService.get_taitsu_persona_system_prompt()
        self.assertIn("Taitsu", persona_prompt)
        self.assertIn("タイツでした。", persona_prompt)

if __name__ == '__main__':
    unittest.main()
