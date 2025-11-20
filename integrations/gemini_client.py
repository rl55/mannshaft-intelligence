"""
Google Gemini API client.
"""

from typing import Dict, Any, Optional, List
import asyncio
import google.generativeai as genai

from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager


class GeminiClient:
    """
    Client for interacting with Google Gemini API.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager
        self.logger = logger.getChild('gemini')
        self.model_name = config.get('gemini.model', 'gemini-pro')
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client."""
        try:
            api_key = config.get('gemini.api_key')
            if not api_key:
                self.logger.warning("Gemini API key not configured")
                return
            
            genai.configure(api_key=api_key)
            self.logger.info(f"Gemini client initialized with model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}", exc_info=True)
    
    async def generate(self, prompt: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate response using Gemini API.
        
        Args:
            prompt: Input prompt
            use_cache: Whether to use cached responses
            
        Returns:
            Response dictionary with text and metadata
        """
        # Check cache first
        if use_cache and self.cache_manager:
            cached = self.cache_manager.get_cached_prompt(prompt, self.model_name)
            if cached:
                self.logger.debug("Using cached Gemini response")
                return {
                    'text': cached['response'],
                    'cached': True,
                    'tokens_input': cached['tokens_input'],
                    'tokens_output': cached['tokens_output']
                }
        
        # Generate new response
        try:
            model = genai.GenerativeModel(self.model_name)
            
            # Run synchronous call in thread pool for async compatibility
            def _generate():
                generation_config = {
                    'temperature': config.get('gemini.temperature', 0.7),
                    'max_output_tokens': config.get('gemini.max_tokens', 2048)
                }
                return model.generate_content(prompt, generation_config=generation_config)
            
            response = await asyncio.to_thread(_generate)
            
            # Extract response
            text = response.text
            tokens_input = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
            tokens_output = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
            
            # Cache the response
            if use_cache and self.cache_manager:
                self.cache_manager.cache_prompt(
                    prompt=prompt,
                    response=text,
                    model=self.model_name,
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    ttl_hours=config.get('cache.prompt_ttl_hours', 168)
                )
            
            return {
                'text': text,
                'cached': False,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output
            }
        except Exception as e:
            self.logger.error(f"Error generating Gemini response: {e}", exc_info=True)
            raise

