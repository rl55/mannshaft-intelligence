"""
Web Search integration for external validation (MCP).
Uses DuckDuckGo as a fallback, can be extended with Google Search API.
"""

from typing import Dict, Any, List, Optional
import aiohttp
import json
from urllib.parse import quote

from utils.config import config
from utils.logger import logger
from cache.cache_manager import CacheManager


class WebSearchClient:
    """
    Client for web search via MCP protocol.
    Uses DuckDuckGo Instant Answer API as fallback.
    Can be extended with Google Custom Search API.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager
        self.logger = logger.getChild('web_search')
        self.google_api_key = config.get('google_search.api_key')
        self.google_cx = config.get('google_search.cx')  # Custom Search Engine ID
        
    async def search(
        self,
        query: str,
        num_results: int = 5,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Perform web search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            use_cache: Whether to use cached results
            
        Returns:
            Search results dictionary
        """
        # Check cache first
        if use_cache and self.cache_manager:
            cache_key = f"web_search:{query}:{num_results}"
            cached = self.cache_manager.get_cached_prompt(
                prompt=cache_key,
                model="web_search"
            )
            if cached:
                self.logger.debug("Using cached search results")
                try:
                    return json.loads(cached['response'])
                except json.JSONDecodeError:
                    pass
        
        # Try Google Custom Search API first
        if self.google_api_key and self.google_cx:
            try:
                results = await self._google_search(query, num_results)
                # Cache results
                if use_cache and self.cache_manager:
                    self.cache_manager.cache_prompt(
                        prompt=cache_key,
                        response=json.dumps(results),
                        model="web_search",
                        tokens_input=0,
                        tokens_output=0,
                        ttl_hours=24
                    )
                return results
            except Exception as e:
                self.logger.warning(f"Google Search failed, using fallback: {e}")
        
        # Fallback to DuckDuckGo
        try:
            results = await self._duckduckgo_search(query, num_results)
            # Cache results
            if use_cache and self.cache_manager:
                self.cache_manager.cache_prompt(
                    prompt=cache_key,
                    response=json.dumps(results),
                    model="web_search",
                    tokens_input=0,
                    tokens_output=0,
                    ttl_hours=24
                )
            return results
        except Exception as e:
            self.logger.error(f"Web search failed: {e}", exc_info=True)
            return {
                'query': query,
                'results': [],
                'error': str(e)
            }
    
    async def _google_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using Google Custom Search API."""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.google_api_key,
            'cx': self.google_cx,
            'q': query,
            'num': min(num_results, 10)  # Google limits to 10
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                for item in data.get('items', [])[:num_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'link': item.get('link', ''),
                        'source': 'google'
                    })
                
                return {
                    'query': query,
                    'results': results,
                    'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                    'source': 'google'
                }
    
    async def _duckduckgo_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using DuckDuckGo Instant Answer API."""
        # DuckDuckGo doesn't have a public API, so we'll use a simple approach
        # In production, consider using duckduckgo-search library or similar
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                
                # Extract abstract if available
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('Heading', query),
                        'snippet': data.get('Abstract', ''),
                        'link': data.get('AbstractURL', ''),
                        'source': 'duckduckgo'
                    })
                
                # Extract related topics
                for topic in data.get('RelatedTopics', [])[:num_results-1]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                            'snippet': topic.get('Text', ''),
                            'link': topic.get('FirstURL', ''),
                            'source': 'duckduckgo'
                        })
                
                return {
                    'query': query,
                    'results': results[:num_results],
                    'total_results': len(results),
                    'source': 'duckduckgo'
                }
    
    async def search_benchmark(
        self,
        metric_name: str,
        industry: str = "SaaS"
    ) -> Dict[str, Any]:
        """
        Search for industry benchmarks.
        
        Args:
            metric_name: Metric to benchmark (e.g., "churn rate", "CSAT score")
            industry: Industry sector
            
        Returns:
            Benchmark information
        """
        query = f"{industry} {metric_name} benchmark industry average"
        return await self.search(query, num_results=3)
    
    async def validate_hypothesis(
        self,
        hypothesis: str
    ) -> Dict[str, Any]:
        """
        Validate a hypothesis with external data.
        
        Args:
            hypothesis: Hypothesis to validate
            
        Returns:
            Validation results
        """
        query = f"{hypothesis} research study data"
        return await self.search(query, num_results=5)

