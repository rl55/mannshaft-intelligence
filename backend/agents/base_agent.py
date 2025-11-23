"""
Base agent abstract class with cache integration.
All agents should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time
import uuid
from datetime import datetime

from cache.cache_manager import CacheManager
from utils.config import config
from utils.logger import logger


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the SaaS BI Agent system.
    
    Provides:
    - Cache integration
    - Tracing and observability
    - Error handling
    - Performance metrics
    """
    
    def __init__(self, agent_type: str, cache_manager: Optional[CacheManager] = None):
        """
        Initialize base agent.
        
        Args:
            agent_type: Type identifier for this agent (e.g., 'revenue', 'product')
            cache_manager: Optional cache manager instance
        """
        self.agent_type = agent_type
        self.cache_manager = cache_manager or CacheManager(
            db_path=config.get('database.path', 'data/agent_cache.db'),
            schema_path=config.get('database.schema_path', 'data/schema.sql')
        )
        self.logger = logger.getChild(self.agent_type)
    
    @abstractmethod
    async def analyze(self, context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Main analysis method to be implemented by subclasses.
        
        Args:
            context: Input context containing data and parameters
            session_id: Session identifier for tracing
            
        Returns:
            Analysis result dictionary with:
            - response: The agent's response text
            - confidence_score: Confidence level (0-1)
            - metadata: Additional metadata
        """
        pass
    
    async def execute(self, context: Dict[str, Any], session_id: str,
                     parent_trace_id: Optional[str] = None,
                     use_cache: bool = True) -> Dict[str, Any]:
        """
        Execute agent with caching, tracing, and error handling.
        
        Args:
            context: Input context
            session_id: Session identifier
            parent_trace_id: Optional parent trace ID for nested calls
            use_cache: Whether to use cached responses
            
        Returns:
            Complete execution result with tracing information
        """
        trace_id = None
        start_time = time.time()
        
        try:
            # Note: Cache check is handled by individual agents after they fetch data
            # and calculate data_hash. BaseAgent doesn't check cache here because
            # the cache context includes data_hash which isn't available until after
            # data is fetched.
            
            # Start trace
            trace_id = self.cache_manager.start_trace(
                agent_type=self.agent_type,
                session_id=session_id,
                parent_trace_id=parent_trace_id
            )
            
            self.logger.info(
                f"Starting {self.agent_type} analysis",
                extra={'trace_id': trace_id, 'session_id': session_id}
            )
            
            # Execute agent analysis
            result = await self.analyze(context, session_id)
            
            # If agent returned cached response, return early (no trace needed)
            if result.get('cached', False):
                return {
                    **result,
                    'trace_id': None  # No trace for cache hits
                }
            
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Note: Caching is handled by individual agents after they fetch data
            # and calculate data_hash. BaseAgent doesn't cache here because the
            # cache context needs to include data_hash which isn't available until
            # after data is fetched by the agent.
            
            # End trace with success
            self.cache_manager.end_trace(
                trace_id=trace_id,
                status='success',
                input_tokens=result.get('input_tokens', 0),
                output_tokens=result.get('output_tokens', 0),
                cached_tokens=result.get('cached_tokens', 0),
                metadata=result.get('metadata')
            )
            
            # Record metrics
            if config.get('monitoring.metrics_enabled', True):
                self.cache_manager.record_metric(
                    metric_name='agent_execution_time_ms',
                    metric_value=execution_time_ms,
                    agent_type=self.agent_type,
                    session_id=session_id
                )
            
            self.logger.info(
                f"Completed {self.agent_type} analysis",
                extra={
                    'trace_id': trace_id,
                    'execution_time_ms': execution_time_ms,
                    'confidence_score': result.get('confidence_score')
                }
            )
            
            return {
                **result,
                'cached': False,
                'execution_time_ms': execution_time_ms,
                'trace_id': trace_id
            }
            
        except Exception as e:
            # Log error
            error_type = type(e).__name__
            error_message = str(e)
            
            self.logger.error(
                f"Error in {self.agent_type} execution",
                extra={
                    'trace_id': trace_id,
                    'error_type': error_type,
                    'error_message': error_message
                },
                exc_info=True
            )
            
            # Log to database
            if trace_id:
                self.cache_manager.log_error(
                    agent_type=self.agent_type,
                    error_type=error_type,
                    error_message=error_message,
                    stack_trace=self._get_stack_trace(e),
                    trace_id=trace_id,
                    context=context,
                    severity='high'
                )
                
                # End trace with error
                self.cache_manager.end_trace(
                    trace_id=trace_id,
                    status='error',
                    error_message=error_message
                )
            
            # Re-raise exception
            raise
    
    def _get_stack_trace(self, exception: Exception) -> str:
        """Get stack trace as string."""
        import traceback
        return traceback.format_exc()
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            'agent_type': self.agent_type,
            'name': self.__class__.__name__,
            'module': self.__class__.__module__
        }

