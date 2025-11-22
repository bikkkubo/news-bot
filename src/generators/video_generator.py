import logging
import datetime
from typing import List, Dict, Any
from src.services.llm_service import LLMService
from src.utils.logger import ExecutionLogger

logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self, llm_service: LLMService, execution_logger: ExecutionLogger):
        self.llm = llm_service
        self.logger = execution_logger

    def generate_script(self, news_items: List[Dict[str, Any]]) -> str:
        """
        Generates the video script in "Taitsu" persona.
        """
        self.logger.log("Generating video script...")
        
        today = datetime.datetime.now().strftime("%Y年%m月%d日")
        
        # Prepare news list for prompt
        news_content = ""
        for i, item in enumerate(news_items[:15], 1):
            news_content += f"News {i}: {item['title']}\nURL: {item['url']}\nDescription: {item['description']}\n\n"

        prompt = f"""
Create a video script for today's financial news ({today}).

News Items:
{news_content}

Requirements:
1. **Persona**: You are "Taitsu". Start with "皆さん、こんにちは。タイツです。"
2. **Structure**:
   - Opening
   - News segments (Introduce each news item clearly).
   - **Image Placeholder**: For EACH news item, insert `[画像を表示: URL]` immediately after the title introduction.
   - Closing: End with "タイツでした。"
3. **Tone**: Professional, engaging, "です・ます".
4. **Language**: Japanese.
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_taitsu_persona_system_prompt())

    def generate_subtitles(self, script: str) -> str:
        """
        Generates subtitles from the script.
        Format: [字幕X] Text...
        """
        self.logger.log("Generating subtitles...")
        
        prompt = f"""
Convert the following video script into a subtitle list.

Script:
{script}

Requirements:
1. **Format**: Each line should start with `[字幕X]` (e.g., `[字幕1]`, `[字幕2]`).
2. **Granularity**: Split long sentences into readable chunks (20-30 chars max per line).
3. **Content**: Keep the exact wording of the script.
4. **Images**: If there is `[画像を表示: URL]`, output it as `[画像X] URL` on its own line.
"""
        return self.llm.generate_text(prompt)
