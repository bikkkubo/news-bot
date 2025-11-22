import os
import logging
import datetime
from typing import List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from src.config import (
    GOOGLE_SERVICE_ACCOUNT_JSON, 
    GOOGLE_DRIVE_FOLDER_ID, 
    SLACK_BOT_TOKEN
)
from src.utils.logger import ExecutionLogger

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, execution_logger: ExecutionLogger):
        self.logger = execution_logger
        self.drive_service = self._initialize_drive_service()
        self.slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

    def _initialize_drive_service(self):
        if not GOOGLE_SERVICE_ACCOUNT_JSON or not os.path.exists(GOOGLE_SERVICE_ACCOUNT_JSON):
            self.logger.log("Google Service Account JSON not found. Drive upload disabled.", level="WARNING")
            return None
        
        try:
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_JSON, scopes=['https://www.googleapis.com/auth/drive.file']
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            self.logger.log(f"Failed to initialize Google Drive service: {e}", level="ERROR")
            return None

    def save_to_local(self, content: str, filename: str, directory: str = "output", sub_dir: str = None) -> str:
        """
        Saves content to a local file. Returns the absolute path.
        """
        # Create directory
        if sub_dir:
            full_dir = os.path.join(directory, sub_dir)
        else:
            today_str = datetime.datetime.now().strftime("%Y%m%d")
            full_dir = os.path.join(directory, today_str)
            
        os.makedirs(full_dir, exist_ok=True)
        
        filepath = os.path.join(full_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.log(f"Saved local file: {filepath}")
            return os.path.abspath(filepath)
        except Exception as e:
            self.logger.log(f"Failed to save local file {filename}: {e}", level="ERROR")
            raise e

    def upload_to_drive(self, file_path: str, folder_id: str = GOOGLE_DRIVE_FOLDER_ID) -> Optional[str]:
        """
        Uploads a file to Google Drive. Returns the file ID.
        """
        if not self.drive_service:
            return None
        
        if not folder_id:
            self.logger.log("Google Drive Folder ID not set. Skipping upload.", level="WARNING")
            return None

        try:
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            self.logger.log(f"Uploaded to Drive: {os.path.basename(file_path)} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            self.logger.log(f"Failed to upload to Drive: {e}", level="ERROR")
            return None

    def upload_to_slack(self, file_paths: List[str], channel_id: str, thread_ts: str = None):
        """
        Uploads multiple files to Slack.
        """
        if not self.slack_client:
            self.logger.log("Slack client not initialized. Skipping upload.", level="WARNING")
            return

        for path in file_paths:
            try:
                response = self.slack_client.files_upload_v2(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    file=path,
                    title=os.path.basename(path),
                    initial_comment=f"Here is the generated file: {os.path.basename(path)}"
                )
                self.logger.log(f"Uploaded to Slack: {os.path.basename(path)}")
            except SlackApiError as e:
                self.logger.log(f"Failed to upload to Slack: {e.response['error']}", level="ERROR")
