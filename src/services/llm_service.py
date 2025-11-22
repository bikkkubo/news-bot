import os
import logging
import json
from typing import Dict, Any, Optional
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic
from src.config import GOOGLE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = self._select_provider()
        self.client = self._initialize_client()
        logger.info(f"LLM Service initialized with provider: {self.provider}")

    def _select_provider(self) -> str:
        # Priority: OpenAI -> Anthropic -> Gemini
        if OPENAI_API_KEY:
            return 'openai'
        elif ANTHROPIC_API_KEY:
            return 'anthropic'
        elif GOOGLE_API_KEY:
            return 'gemini'
        else:
            raise ValueError("No LLM API key found")

    def _initialize_client(self):
        if self.provider == 'openai':
            return OpenAI(api_key=OPENAI_API_KEY)
        elif self.provider == 'anthropic':
            return Anthropic(api_key=ANTHROPIC_API_KEY)
        elif self.provider == 'gemini':
            genai.configure(api_key=GOOGLE_API_KEY)
            # Switching to stable Pro model to avoid 404/Quota errors with experimental versions
            return genai.GenerativeModel('gemini-1.5-pro') 

    def generate_text(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        if self.provider == 'openai':
            try:
                return self._generate_with_openai(prompt, system_prompt, temperature)
            except Exception as e:
                logger.warning(f"OpenAI generation failed: {e}")
                if ANTHROPIC_API_KEY:
                    logger.info("Falling back to Anthropic (Claude)...")
                    return self._generate_with_anthropic(prompt, system_prompt, temperature)
                elif GOOGLE_API_KEY:
                    logger.info("Falling back to Gemini...")
                    return self._generate_with_gemini(prompt, system_prompt)
                else:
                    raise e

        elif self.provider == 'anthropic':
            try:
                return self._generate_with_anthropic(prompt, system_prompt, temperature)
            except Exception as e:
                logger.warning(f"Anthropic generation failed: {e}")
                if GOOGLE_API_KEY:
                    logger.info("Falling back to Gemini...")
                    return self._generate_with_gemini(prompt, system_prompt)
                else:
                    raise e
        
        elif self.provider == 'gemini':
             # Gemini is last resort in this config, but if selected as primary (no other keys), it runs here
            return self._generate_with_gemini(prompt, system_prompt)

    def _generate_with_gemini(self, prompt: str, system_prompt: str = None) -> str:
        # Gemini doesn't have a separate system prompt in the same way, usually prepended
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self.client.generate_content(full_prompt)
        return response.text

    def _generate_with_openai(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        # Ensure we have a client if falling back
        client = self.client if self.provider == 'openai' else OpenAI(api_key=OPENAI_API_KEY)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            # Reverting to stable model
            model="gpt-4o",
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

    def _generate_with_anthropic(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {
            # Reverting to stable model
            model="claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "messages": messages,
            "temperature": temperature
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def generate_json(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Generate JSON output. 
        Note: For robust JSON generation, we might need provider-specific 'json_mode' or parsing.
        """
        json_prompt = f"{prompt}\n\nIMPORTANT: Output ONLY valid JSON."
        response_text = self.generate_text(json_prompt, system_prompt, temperature=0.2)
        
        # Clean up markdown code blocks if present
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {cleaned_text}")
            raise e

    # --- Prompts ---

    @staticmethod
    def get_fact_extraction_system_prompt() -> str:
        return """
You are a strict financial analyst AI. Your task is to extract and report financial news based ONLY on the provided source text.

CRITICAL RULES:
1. **FACTS ONLY**: Report only confirmed facts, numbers, and official announcements.
2. **NO OPINIONS**: Remove all analyst opinions, predictions, personal views, and "market sentiment" fluff unless it is a direct quote of a significant figure (e.g., Fed Chair).
3. **NO HALLUCINATIONS**: Do not invent any details. If it's not in the text, do not write it.
4. **SOURCE ATTRIBUTION**: You must embed the source URL in the text using the format `([Source Name](URL))`.
5. **MARKET NAMES**: Use specific market names (e.g., "ナスダック総合指数" instead of "ナスダック").
6. **LANGUAGE**: Output in Japanese.
"""

    @staticmethod
    def get_taitsu_persona_system_prompt() -> str:
        return """
You are "Taitsu" (タイツ), a charismatic and professional financial news presenter.

PERSONA RULES:
1. **TONE**: Use polite Japanese ("です・ます" tone). Professional yet engaging.
2. **CATCHPHRASE**: Always end the script with "タイツでした。" (Taitsu deshita).
3. **INTRO**: Start with "皆さん、こんにちは。タイツです。" (Hello everyone, I am Taitsu).
4. **FORMAT**:
   - Use `[画像を表示: URL]` to indicate where an image should be shown.
   - The script must be readable and suitable for a video voiceover.
"""
