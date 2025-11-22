import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock slack_bolt.App BEFORE importing src.bot to prevent auth check
with patch('slack_bolt.App') as mock_app_cls:
    # Mock environment variables
    with patch.dict(os.environ, {
        'NEWSAPI_KEY': 'test_key',
        'GOOGLE_API_KEY': 'test_key',
        'SLACK_BOT_TOKEN': 'test_token',
        'SLACK_APP_TOKEN': 'test_token',
        'SLACK_CHANNEL_ID': 'C12345'
    }):
        from src.bot import run_report_generation

class TestIntegration(unittest.TestCase):
    
    @patch('src.bot.StockDataCollector')
    @patch('src.bot.NewsDataCollector')
    @patch('src.bot.LLMService')
    @patch('src.bot.FileManager')
    # We don't need to patch app here again for the import, but we might need to patch the 'app' instance in src.bot
    # However, since we mocked the class App during import, src.bot.app is already a mock.
    def test_full_pipeline(self, mock_file_manager_cls, mock_llm_cls, mock_news_cls, mock_stock_cls):
        # Mock dependencies
        mock_stock_instance = mock_stock_cls.return_value
        mock_stock_instance.fetch_stock_prices.return_value = {
            "ナスダック総合指数": {"close": 100, "change": 1, "change_pct": 1.0}
        }
        
        mock_news_instance = mock_news_cls.return_value
        mock_news_instance.fetch_news.return_value = [
            {
                "title": "Test News",
                "url": "http://reuters.com/test",
                "source": "Reuters",
                "description": "Test description",
                "content": "Test content"
            }
        ]
        
        mock_llm_instance = mock_llm_cls.return_value
        mock_llm_instance.generate_text.return_value = "Generated Content"
        
        mock_file_manager_instance = mock_file_manager_cls.return_value
        mock_file_manager_instance.save_to_local.return_value = "/tmp/test_file.txt"
        
        # Mock Slack 'say' function
        mock_say = MagicMock()
        
        # Run pipeline
        run_report_generation(mock_say, "thread_ts_123")
        
        # Assertions
        # 1. Check if data was collected
        mock_stock_instance.fetch_stock_prices.assert_called_once()
        mock_news_instance.fetch_news.assert_called_once()
        
        # 2. Check if LLM was called for report, script, and subtitles
        # We expect generate_text to be called multiple times
        self.assertTrue(mock_llm_instance.generate_text.call_count >= 3)
        
        # 3. Check if files were saved
        self.assertTrue(mock_file_manager_instance.save_to_local.call_count >= 4) # Report, Script, Subs, Log
        
        # 4. Check if uploaded to Slack
        mock_file_manager_instance.upload_to_slack.assert_called_once()
        
        # 5. Check if completion message was sent
        mock_say.assert_any_call(text="✅ レポート生成が完了しました！", thread_ts="thread_ts_123")

if __name__ == '__main__':
    unittest.main()
