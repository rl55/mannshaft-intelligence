"""
Base Agent Abstract Class for SaaS BI Agent System.
Provides common functionality for all specialized agents with cache integration.
"""

import time
import json
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

from cache.cache_manager import CacheManager
from utils.logger import get_logger, set_trace_context
from utils.config import get_config


@dataclass
class AgentResponse:
    """Standard response format for all agents."""
    success: bool
    data: Any
    confidence: float
    cached: bool
    trace_id: str
    execution_time_ms: int
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """
    Abstract base class for all SaaS BI agents.

    Provides:
    - Automatic caching (prompt-level and agent-level)
    - Distributed tracing
    - Error handling and logging
    - Performance metrics
    - Configuration management

    Subclasses must implement:
    - _generate_analysis(): Core analysis logic
    - _build_prompt(): Prompt construction
    - _calculate_confidence(): Confidence scoring
    """

    def __init__(
        self,
        agent_type: str,
        cache_manager: CacheManager,
        model: Optional[str] = None
    ):
        """
        Initialize base agent.

        Args:
            agent_type: Type identifier for this agent (e.g., 'revenue', 'product')
            cache_manager: Shared cache manager instance
            model: Optional model override (defaults to config)
        """
        self.agent_type = agent_type
        self.cache = cache_manager
        self.config = get_config()
        self.logger = get_logger(f"agent.{agent_type}")

        # Get model from config if not provided
        if model is None:
            model = self.config.gemini.model

        self.model = model

        # Get agent-specific configuration
        self.agent_config = self.config.get_agent_config(agent_type)

        # Load thresholds from config
        self.confidence_threshold = self.agent_config.get('confidence_threshold', 0.7)
        self.max_data_points = self.agent_config.get('max_data_points', 1000)

        self.logger.info(
            f"Initialized {agent_type} agent with model {model}",
            extra_data={'agent_type': agent_type, 'model': model}
        )

    def execute(
        self,
        data: Dict[str, Any],
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        skip_cache: bool = False
    ) -> AgentResponse:
        """
        Execute agent analysis with full observability and caching.

        This is the main entry point for all agents. It handles:
        - Cache checking (agent-level)
        - Tracing
        - Error handling
        - Metrics collection
        - Response caching

        Args:
            data: Input data for analysis
            session_id: Current session ID
            context: Optional additional context
            skip_cache: If True, bypass cache and force new generation

        Returns:
            AgentResponse with results
        """
        # Start trace
        trace_id = self.cache.start_trace(
            agent_type=self.agent_type,
            session_id=session_id
        )

        # Set trace context for logging
        set_trace_context(trace_id=trace_id, session_id=session_id)

        start_time = time.time()

        try:
            self.logger.info(
                f"Starting {self.agent_type} agent execution",
                extra_data={
                    'trace_id': trace_id,
                    'session_id': session_id,
                    'skip_cache': skip_cache
                }
            )

            # Check agent-level cache first (unless skip_cache is True)
            if not skip_cache:
                cached_result = self._check_cache(data, context)
                if cached_result:
                    execution_time_ms = int((time.time() - start_time) * 1000)

                    self.logger.info(
                        f"Cache HIT for {self.agent_type} agent",
                        extra_data={'trace_id': trace_id, 'cache_hit': True}
                    )

                    # End trace with cache hit
                    self.cache.end_trace(
                        trace_id=trace_id,
                        status='success',
                        cached_tokens=self._estimate_tokens(data),
                        metadata={'cache_hit': True, 'from_cache': True}
                    )

                    return AgentResponse(
                        success=True,
                        data=cached_result['data'],
                        confidence=cached_result['confidence'],
                        cached=True,
                        trace_id=trace_id,
                        execution_time_ms=execution_time_ms,
                        metadata={'from_cache': True}
                    )

            self.logger.info(
                f"Cache MISS for {self.agent_type} agent - generating new analysis",
                extra_data={'trace_id': trace_id, 'cache_hit': False}
            )

            # Validate input data
            self._validate_input(data)

            # Generate new analysis
            analysis_result = self._generate_analysis(data, context, trace_id)

            # Calculate confidence
            confidence_score = self._calculate_confidence(data, analysis_result, context)

            # Check if confidence meets threshold
            if confidence_score < self.confidence_threshold:
                self.logger.warning(
                    f"Low confidence score: {confidence_score}",
                    extra_data={
                        'trace_id': trace_id,
                        'confidence': confidence_score,
                        'threshold': self.confidence_threshold
                    }
                )

            # Cache the response (unless skip_cache is True)
            execution_time_ms = int((time.time() - start_time) * 1000)
            if not skip_cache:
                self._save_to_cache(
                    data=data,
                    context=context,
                    result=analysis_result,
                    confidence=confidence_score,
                    execution_time_ms=execution_time_ms
                )

            # End trace successfully
            input_tokens, output_tokens = self._estimate_token_usage(data, analysis_result)
            self.cache.end_trace(
                trace_id=trace_id,
                status='success',
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                metadata={
                    'cache_hit': False,
                    'confidence': confidence_score,
                    'data_size': len(str(data))
                }
            )

            # Record performance metric
            self.cache.record_metric(
                metric_name=f'{self.agent_type}_latency_ms',
                metric_value=execution_time_ms,
                agent_type=self.agent_type,
                session_id=session_id,
                dimensions={'confidence': confidence_score}
            )

            self.logger.info(
                f"{self.agent_type} agent execution completed",
                extra_data={
                    'trace_id': trace_id,
                    'execution_time_ms': execution_time_ms,
                    'confidence': confidence_score
                }
            )

            return AgentResponse(
                success=True,
                data=analysis_result,
                confidence=confidence_score,
                cached=False,
                trace_id=trace_id,
                execution_time_ms=execution_time_ms,
                metadata={
                    'from_cache': False,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens
                }
            )

        except Exception as e:
            # Log error
            error_msg = str(e)
            stack_trace = traceback.format_exc()

            self.logger.error(
                f"Error in {self.agent_type} agent",
                exc_info=True,
                extra_data={
                    'trace_id': trace_id,
                    'error_type': type(e).__name__
                }
            )

            self.cache.log_error(
                agent_type=self.agent_type,
                error_type=type(e).__name__,
                error_message=error_msg,
                stack_trace=stack_trace,
                trace_id=trace_id,
                context={'data_keys': list(data.keys()) if isinstance(data, dict) else None},
                severity='high'
            )

            # End trace with error
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.cache.end_trace(
                trace_id=trace_id,
                status='error',
                error_message=error_msg
            )

            return AgentResponse(
                success=False,
                data=None,
                confidence=0.0,
                cached=False,
                trace_id=trace_id,
                execution_time_ms=execution_time_ms,
                error=error_msg
            )

    def _check_cache(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check agent-level cache for existing response.

        Args:
            data: Input data
            context: Additional context

        Returns:
            Cached response or None
        """
        cache_context = self._build_cache_context(data, context)
        cached_response = self.cache.get_cached_agent_response(
            agent_type=self.agent_type,
            context=cache_context
        )

        if cached_response:
            try:
                return {
                    'data': json.loads(cached_response['response']),
                    'confidence': cached_response['confidence_score']
                }
            except json.JSONDecodeError:
                self.logger.warning("Failed to decode cached response")
                return None

        return None

    def _save_to_cache(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        result: Any,
        confidence: float,
        execution_time_ms: int
    ):
        """
        Save response to agent-level cache.

        Args:
            data: Input data
            context: Additional context
            result: Analysis result
            confidence: Confidence score
            execution_time_ms: Execution time
        """
        cache_context = self._build_cache_context(data, context)
        ttl_hours = self.config.cache.agent_response_ttl_hours

        self.cache.cache_agent_response(
            agent_type=self.agent_type,
            context=cache_context,
            response=json.dumps(result),
            confidence_score=confidence,
            execution_time_ms=execution_time_ms,
            ttl_hours=ttl_hours
        )

    def _build_cache_context(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build cache context from data and additional context.

        Args:
            data: Input data
            context: Additional context

        Returns:
            Combined context for cache key
        """
        cache_context = {
            'data': data,
            'model': self.model
        }

        if context:
            cache_context['context'] = context

        return cache_context

    def _validate_input(self, data: Dict[str, Any]):
        """
        Validate input data.

        Args:
            data: Input data to validate

        Raises:
            ValueError: If validation fails
        """
        if not data:
            raise ValueError("Input data cannot be empty")

        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")

        # Check data point limit
        if 'records' in data:
            record_count = len(data['records'])
            if record_count > self.max_data_points:
                raise ValueError(
                    f"Too many data points: {record_count} exceeds limit of {self.max_data_points}"
                )

    def _estimate_tokens(self, data: Dict[str, Any]) -> int:
        """
        Estimate token count for data.

        Args:
            data: Data to estimate

        Returns:
            Estimated token count
        """
        # Rough estimation: ~1.3 tokens per word
        text = json.dumps(data)
        words = len(text.split())
        return int(words * 1.3)

    def _estimate_token_usage(
        self,
        data: Dict[str, Any],
        result: Any
    ) -> tuple[int, int]:
        """
        Estimate input and output token usage.

        Args:
            data: Input data
            result: Output result

        Returns:
            (input_tokens, output_tokens)
        """
        input_tokens = self._estimate_tokens(data)
        output_tokens = self._estimate_tokens({'result': result})
        return input_tokens, output_tokens

    # =========================================================================
    # ABSTRACT METHODS - Must be implemented by subclasses
    # =========================================================================

    @abstractmethod
    def _generate_analysis(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        trace_id: str
    ) -> Any:
        """
        Generate analysis result. Must be implemented by subclasses.

        Args:
            data: Input data
            context: Additional context
            trace_id: Current trace ID

        Returns:
            Analysis result (format depends on agent type)
        """
        pass

    @abstractmethod
    def _build_prompt(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for LLM. Must be implemented by subclasses.

        Args:
            data: Input data
            context: Additional context

        Returns:
            Formatted prompt string
        """
        pass

    @abstractmethod
    def _calculate_confidence(
        self,
        data: Dict[str, Any],
        result: Any,
        context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score. Must be implemented by subclasses.

        Args:
            data: Input data
            result: Analysis result
            context: Additional context

        Returns:
            Confidence score (0.0 to 1.0)
        """
        pass
