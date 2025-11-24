import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("execution.log"),
        logging.StreamHandler()
    ]
)

# LLM Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# News API
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C09S2KBK3HU")

# Google Drive
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Constants
MARKET_NAMES = {
    "DOW": "ダウ平均株価",
    "NASDAQ": "ナスダック総合指数",
    "SP500": "S&P 500",
    "NIKKEI": "日経平均株価"
}

ALLOWED_NEWS_SOURCES = [
    "reuters",
    "bloomberg",
    "the-wall-street-journal"
]

EXCLUDED_KEYWORDS = [
    "gift", "travel", "cruise", "review", "best of", "lifestyle", 
    "sport", "entertainment", "fashion", "movie", "music", 
    "recipe", "food", "drink", "vacation", "holiday", "guide",
    "deal of the day", "shopping", "workout", "health"
]

NON_US_KEYWORDS = [
    "uk", "britain", "london", "england", "europe", "eu", "german", "france", 
    "ecb", "bank of england", "brexit"
]

# Validation
def validate_config():
    missing = []
    if not any([GOOGLE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY]):
        missing.append("One of GOOGLE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY")
    if not NEWSAPI_KEY:
        missing.append("NEWSAPI_KEY")
    if not SLACK_BOT_TOKEN:
        missing.append("SLACK_BOT_TOKEN")
    if not SLACK_APP_TOKEN:
        missing.append("SLACK_APP_TOKEN")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

if __name__ == "__main__":
    try:
        validate_config()
        print("Configuration valid.")
    except ValueError as e:
        print(f"Configuration error: {e}")
