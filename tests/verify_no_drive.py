import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging to capture output
import logging
logging.basicConfig(level=logging.INFO)

class TestNoDriveConfig(unittest.TestCase):
    
    @patch('src.collectors.stock_collector.StockDataCollector')
    @patch('src.collectors.news_collector.NewsDataCollector')
    @patch('src.services.llm_service.LLMService')
    @patch('src.managers.file_manager.WebClient') # Patch WebClient to prevent real Slack calls in FileManager
    def test_pipeline_without_drive(self, mock_web_client, mock_llm_cls, mock_news_cls, mock_stock_cls):
        
        # Set environment variables: Valid for others, Empty/Invalid for Drive
        env_vars = {
            'NEWSAPI_KEY': 'test_key',
            'GOOGLE_API_KEY': 'test_key',
            'SLACK_BOT_TOKEN': 'test_token',
            'SLACK_APP_TOKEN': 'test_token',
            'SLACK_CHANNEL_ID': 'C12345',
            'GOOGLE_SERVICE_ACCOUNT_JSON': '', # Empty
            'GOOGLE_DRIVE_FOLDER_ID': ''       # Empty
        }
        
        # Mock slack_bolt.App BEFORE importing src.bot
        with patch('slack_bolt.App'), patch.dict(os.environ, env_vars):
            # Import inside patch to pick up env vars and mocked App
            import src.bot
            import importlib
            importlib.reload(src.bot) # Ensure fresh import with mocked App
            
            # DOUBLE CHECK: Force app to be a mock to prevent ANY real calls
            src.bot.app = MagicMock()
            
            from src.bot import run_report_generation
            
            # Mock dependencies to return dummy data
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
            
            # Mock Slack say
            mock_say = MagicMock()
            
            print("\n--- Running Pipeline with NO Drive Credentials ---")
            # Run the pipeline
            run_report_generation(mock_say, "thread_ts_test")
            print("--- Pipeline Finished ---")
            
            # Debug: Print all calls to say
            print("\n[Debug] mock_say calls:")
            for call in mock_say.call_args_list:
                print(call)

            # Assertions
            # 1. Check if completion message was sent (means it didn't crash)
            mock_say.assert_any_call(text="✅ レポート生成が完了しました！", thread_ts="thread_ts_test")
            
            # 2. Verify Drive upload was skipped (we can't easily check internal state of FileManager here without more mocks, 
            # but the fact it finished without error is the main test)

if __name__ == '__main__':
    unittest.main()
