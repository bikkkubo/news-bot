import logging
import os
import sys
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Mock Slack App to avoid token errors if not set
with patch('slack_bolt.App'):
    from src.bot import run_report_generation

def mock_say(text, thread_ts=None):
    print(f"\n[Slack Bot Message]: {text}\n")

if __name__ == "__main__":
    print("--- Starting Manual Execution ---")
    
    # Check for .env
    if not os.path.exists(".env"):
        print("WARNING: .env file not found. Execution might fail if API keys are missing.")
    
    try:
        run_report_generation(mock_say, "manual_run_thread_id")
        print("--- Manual Execution Finished ---")
    except Exception as e:
        print(f"--- Manual Execution Failed: {e} ---")
