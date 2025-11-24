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
   - Opening: Brief market overview.
   - News segments:
     - **Hook**: Start with a compelling question or statement.
     - **Core Fact**: What happened? (Concise)
     - **Deep Dive (CRITICAL)**: Explain *WHY* this matters. What is the context? What are the implications? (Like a tech visionary explaining the future).
     - **Image Placeholder**: Insert `[画像を表示: URL]` at relevant points.
   - Closing: End with "タイツでした。"
3. **Tone**: Professional, insightful, visionary, yet accessible ("です・ます").
4. **Content Depth**: Do NOT just read the news. Provide *interpretation* and *insight*. Connect the dots for the viewer.
5. **Language**: Japanese.
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_taitsu_persona_system_prompt())

    def generate_subtitles(self, script: str) -> str:
        """
        Generates visual slide text (titles/bullets) from the script.
        """
        self.logger.log("Generating slide text...")
        
        prompt = f"""
Convert the following video narration script into "Visual Slide Text" for a video.
The goal is to create text that can be copy-pasted into video slides (like PowerPoint or YouTube text overlays).

Script:
{script}

Requirements:
1. **Format**: Group by scenes/news items.
   - Use `[スライドX]` to mark a new visual scene.
2. **Content**:
   - **Title**: A short, catchy headline for the slide.
   - **Body**: 3-4 concise bullet points summarizing the key information.
   - **Visuals**: Keep `[画像を表示: URL]` tags where they appear.
3. **Style**: Concise, high-impact text. NO long sentences. Use noun phrases (体言止め) where appropriate.
4. **Relationship**: The Slide Text should be the "visual summary" of what is being spoken in the script.

Example Output:
[スライド1]
タイトル: 米国市場、大幅反発
- ダウ平均 500ドル高
- インフレ懸念が後退
- テック株が主導
[画像を表示: URL]
"""
        return self.llm.generate_text(prompt, system_prompt=self.llm.get_taitsu_persona_system_prompt())
