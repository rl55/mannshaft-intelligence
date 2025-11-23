"""
Google Gemini API client.
"""

from typing import Dict, Any, Optional, List
import asyncio
import json
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
        self.model_name = config.get('gemini.model', 'gemini-2.5-flash-lite')
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client."""
        try:
            api_key = config.get('gemini.api_key')
            if not api_key:
                self.logger.warning("Gemini API key not configured")
                return
            
            genai.configure(api_key=api_key)
            
            # Try to list available models to find a working one
            try:
                available_models = [m.name for m in genai.list_models()]
                self.logger.info(f"Available Gemini models: {available_models}")
                
                # Check if configured model is available
                # Model names in the list are full paths like "models/gemini-1.5-flash"
                model_available = any(self.model_name in m or f"models/{self.model_name}" == m for m in available_models)
                if not model_available:
                    # Try to find a compatible model (free tier models prioritized)
                    # All these models are free tier: gemini-2.5-flash-lite, gemini-2.0-flash-lite, gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro
                    fallback_models = ['gemini-2.5-flash-lite', 'gemini-2.0-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
                    for fallback in fallback_models:
                        if any(fallback in m or f"models/{fallback}" == m for m in available_models):
                            self.logger.warning(
                                f"Configured model '{self.model_name}' not available. "
                                f"Using fallback: {fallback}"
                            )
                            self.model_name = fallback
                            break
            except Exception as e:
                self.logger.warning(f"Could not list available models: {e}. Using configured model.")
            
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
            # Try to use the model, with fallback if it fails
            model = None
            response = None
            
            # Try configured model first
            try:
                model = genai.GenerativeModel(self.model_name)
                def _generate():
                    generation_config = {
                        'temperature': config.get('gemini.temperature', 0.7),
                        'max_output_tokens': config.get('gemini.max_tokens', 2048)
                    }
                    return model.generate_content(prompt, generation_config=generation_config)
                response = await asyncio.to_thread(_generate)
            except Exception as model_error:
                error_str = str(model_error)
                # If model not found or quota exceeded, try fallback models
                if "404" in error_str or "not found" in error_str.lower() or "429" in error_str or "quota" in error_str.lower():
                    self.logger.warning(f"Model {self.model_name} not available or quota exceeded, trying fallback models...")
                    # All these models are free tier compatible (free of charge)
                    # Prioritize newer models first, then fall back to older ones
                    fallback_models = ['gemini-2.5-flash-lite', 'gemini-2.0-flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
                    
                    for fallback_model in fallback_models:
                        if fallback_model == self.model_name:
                            continue  # Skip the model that already failed
                        try:
                            self.logger.info(f"Trying fallback model: {fallback_model}")
                            model = genai.GenerativeModel(fallback_model)
                            def _generate_fallback():
                                generation_config = {
                                    'temperature': config.get('gemini.temperature', 0.7),
                                    'max_output_tokens': config.get('gemini.max_tokens', 2048)
                                }
                                return model.generate_content(prompt, generation_config=generation_config)
                            response = await asyncio.to_thread(_generate_fallback)
                            self.logger.info(f"Successfully used fallback model: {fallback_model}")
                            # Update model name for caching
                            self.model_name = fallback_model
                            break
                        except Exception as fallback_error:
                            fallback_error_str = str(fallback_error)
                            if "429" in fallback_error_str or "quota" in fallback_error_str.lower():
                                self.logger.warning(f"Fallback model {fallback_model} also has quota issues, skipping...")
                            else:
                                self.logger.debug(f"Fallback model {fallback_model} also failed: {fallback_error}")
                            continue
                    
                    if response is None:
                        raise Exception(f"All model attempts failed. Original error: {model_error}")
                else:
                    raise
            
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

