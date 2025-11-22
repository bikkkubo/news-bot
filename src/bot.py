import os
import logging
import threading
import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from src.config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_CHANNEL_ID
from src.utils.logger import ExecutionLogger
from src.collectors.stock_collector import StockDataCollector
from src.collectors.news_collector import NewsDataCollector
from src.services.llm_service import LLMService
from src.generators.report_generator import ReportGenerator
from src.generators.video_generator import VideoGenerator
from src.managers.file_manager import FileManager

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack App
app = App(token=SLACK_BOT_TOKEN)

def run_report_generation(say, thread_ts):
    """
    Orchestrates the full report generation pipeline.
    """
    execution_logger = ExecutionLogger()
    execution_logger.log("Starting V7.2 News Report System...")
    
    try:
        # 1. Initialize Components
        stock_collector = StockDataCollector()
        news_collector = NewsDataCollector()
        llm_service = LLMService()
        report_generator = ReportGenerator(llm_service, execution_logger)
        video_generator = VideoGenerator(llm_service, execution_logger)
        file_manager = FileManager(execution_logger)

        # 2. Data Collection
        say(text="⏳ 株価データを取得中...", thread_ts=thread_ts)
        stock_data = stock_collector.fetch_stock_prices()
        execution_logger.log(f"Stock data fetched: {list(stock_data.keys())}")
        
        say(text="⏳ ニュースデータを収集中 (Reuters, Bloomberg, WSJ)...", thread_ts=thread_ts)
        news_items = news_collector.fetch_news()
        execution_logger.log(f"News items fetched: {len(news_items)}")
        
        if not news_items:
            say(text="⚠️ ニュースが見つかりませんでした。処理を中止します。", thread_ts=thread_ts)
            return

        # 3. Report Generation
        say(text="⏳ レポートと深堀り分析を生成中...", thread_ts=thread_ts)
        report_md = report_generator.generate_report(stock_data, news_items)
        
        # 4. Video Content Generation
        say(text="⏳ 動画用台本と字幕を生成中 (タイツ風)...", thread_ts=thread_ts)
        script_txt = video_generator.generate_script(news_items)
        subtitles_txt = video_generator.generate_subtitles(script_txt)

        # 5. Save Files
        say(text="⏳ ファイルを保存・アップロード中...", thread_ts=thread_ts)
        saved_files = []
        
        # Generate timestamp for naming: YYYYMMDD_H:mm
        # Note: H:mm might be tricky on Windows but OK on Mac/Linux.
        now = datetime.datetime.fromtimestamp(execution_logger.start_time)
        timestamp_str = now.strftime("%Y%m%d_%H:%M")
        
        # Save Markdown Report
        report_filename = f"{timestamp_str}_report.md"
        report_path = file_manager.save_to_local(report_md, report_filename, sub_dir=timestamp_str)
        saved_files.append(report_path)
        
        # Save Script
        script_filename = f"{timestamp_str}_script.txt"
        script_path = file_manager.save_to_local(script_txt, script_filename, sub_dir=timestamp_str)
        saved_files.append(script_path)
        
        # Save Subtitles
        subtitles_filename = f"{timestamp_str}_subtitles.txt"
        subtitles_path = file_manager.save_to_local(subtitles_txt, subtitles_filename, sub_dir=timestamp_str)
        saved_files.append(subtitles_path)
        
        # Save Execution Log
        execution_logger.save()
        log_filename = f"{timestamp_str}_log.txt"
        log_path = file_manager.save_to_local(execution_logger.get_logs(), log_filename, sub_dir=timestamp_str)
        saved_files.append(log_path)

        # 6. Upload to Drive
        for path in saved_files:
            file_manager.upload_to_drive(path)

        # 7. Upload to Slack
        file_manager.upload_to_slack(saved_files, SLACK_CHANNEL_ID, thread_ts)

        # 8. Finish
        say(text="✅ レポート生成が完了しました！", thread_ts=thread_ts)
        app.client.reactions_add(
            channel=SLACK_CHANNEL_ID,
            name="white_check_mark",
            timestamp=thread_ts
        )

    except Exception as e:
        error_msg = f"❌ エラーが発生しました: {str(e)}"
        logger.error(error_msg)
        say(text=error_msg, thread_ts=thread_ts)
        app.client.reactions_add(
            channel=SLACK_CHANNEL_ID,
            name="x",
            timestamp=thread_ts
        )
        # Try to save log even if failed
        try:
            execution_logger.log(f"Critical Failure: {e}", level="ERROR")
            execution_logger.save()
        except:
            pass

@app.event("app_mention")
def handle_mention(event, say):
    """
    Triggered when the bot is mentioned.
    """
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])
    
    # Verify channel
    if channel != SLACK_CHANNEL_ID:
        say(text=f"このチャンネル ({channel}) では利用できません。指定されたチャンネル ({SLACK_CHANNEL_ID}) で実行してください。", thread_ts=thread_ts)
        return

    # React with eyes
    try:
        app.client.reactions_add(
            channel=channel,
            name="eyes",
            timestamp=event["ts"]
        )
    except Exception as e:
        logger.warning(f"Failed to add reaction: {e}")

    say(text="🚀 ニュースレポート生成を開始します...", thread_ts=thread_ts)

    # Run in a separate thread to prevent timeout
    thread = threading.Thread(target=run_report_generation, args=(say, thread_ts))
    thread.start()

if __name__ == "__main__":
    if not SLACK_APP_TOKEN:
        print("SLACK_APP_TOKEN is missing.")
    else:
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
