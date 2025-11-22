import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLLMFallback(unittest.TestCase):
    
    @patch('src.services.llm_service.OpenAI')
    @patch('src.services.llm_service.genai')
    def test_gemini_fallback_to_openai(self, mock_genai, mock_openai_cls):
        # Setup Environment
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'test_google_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }):
            from src.services.llm_service import LLMService
            
            # Setup Gemini Mock to FAIL
            mock_genai_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_genai_model
            mock_genai_model.generate_content.side_effect = Exception("Quota exceeded")
            
            # Setup OpenAI Mock to SUCCEED
            mock_openai_instance = mock_openai_cls.return_value
            mock_openai_instance.chat.completions.create.return_value.choices[0].message.content = "Fallback Success"
            
            # Initialize Service (should pick Gemini first)
            service = LLMService()
            self.assertEqual(service.provider, 'gemini')
            
            # Execute Generation
            result = service.generate_text("Test Prompt")
            
            # Assertions
            # 1. Verify Gemini was called
            mock_genai_model.generate_content.assert_called_once()
            
            # 2. Verify OpenAI was called
            mock_openai_cls.assert_called_once() # Client initialized
            mock_openai_instance.chat.completions.create.assert_called_once()
            
            # 3. Verify Result
            self.assertEqual(result, "Fallback Success")

if __name__ == '__main__':
    unittest.main()
