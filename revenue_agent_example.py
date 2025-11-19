"""
SaaS BI Agent - Revenue Agent Example
Demonstrates integration with CacheManager for caching, tracing, and observability
"""

import time
from typing import Dict, Any, Optional
import json
from utils.cache_manager import CacheManager


class RevenueAgent:
    """
    Revenue Analysis Agent with full CacheManager integration.
    
    Analyzes MRR, churn, ARPU, and other revenue metrics with:
    - Prompt and response caching
    - Distributed tracing
    - Error handling and logging
    - Performance metrics
    """
    
    def __init__(self, cache_manager: CacheManager, model: str = "gemini-2.0-flash"):
        self.cache = cache_manager
        self.model = model
        self.agent_type = "revenue"
    
    def analyze(self, revenue_data: Dict[str, Any], session_id: str,
                analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Perform revenue analysis with full observability.
        
        Args:
            revenue_data: Revenue metrics data
            session_id: Current session ID
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results with metadata
        """
        # Start trace
        trace_id = self.cache.start_trace(
            agent_type=self.agent_type,
            session_id=session_id
        )
        
        start_time = time.time()
        
        try:
            # Check agent-level cache first
            context = {
                "data": revenue_data,
                "analysis_type": analysis_type,
                "model": self.model
            }
            
            cached_response = self.cache.get_cached_agent_response(
                agent_type=self.agent_type,
                context=context
            )
            
            if cached_response:
                print(f"✓ Cache HIT for {self.agent_type} agent")
                
                # End trace with cache hit
                execution_time_ms = int((time.time() - start_time) * 1000)
                self.cache.end_trace(
                    trace_id=trace_id,
                    status='success',
                    cached_tokens=100,  # Estimate
                    metadata={'cache_hit': True, 'analysis_type': analysis_type}
                )
                
                return {
                    'analysis': cached_response['response'],
                    'confidence': cached_response['confidence_score'],
                    'cached': True,
                    'trace_id': trace_id
                }
            
            print(f"✗ Cache MISS for {self.agent_type} agent - generating new analysis")
            
            # Generate new analysis
            analysis_result = self._generate_analysis(
                revenue_data=revenue_data,
                analysis_type=analysis_type,
                trace_id=trace_id
            )
            
            # Calculate confidence
            confidence_score = self._calculate_confidence(revenue_data, analysis_result)
            
            # Cache the response
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.cache.cache_agent_response(
                agent_type=self.agent_type,
                context=context,
                response=json.dumps(analysis_result),
                confidence_score=confidence_score,
                execution_time_ms=execution_time_ms,
                ttl_hours=24
            )
            
            # End trace successfully
            self.cache.end_trace(
                trace_id=trace_id,
                status='success',
                input_tokens=500,  # Estimate
                output_tokens=1500,  # Estimate
                metadata={
                    'cache_hit': False,
                    'analysis_type': analysis_type,
                    'data_points': len(revenue_data.get('records', []))
                }
            )
            
            # Record performance metric
            self.cache.record_metric(
                metric_name='analysis_latency_ms',
                metric_value=execution_time_ms,
                agent_type=self.agent_type,
                session_id=session_id,
                dimensions={'analysis_type': analysis_type}
            )
            
            return {
                'analysis': analysis_result,
                'confidence': confidence_score,
                'cached': False,
                'trace_id': trace_id,
                'execution_time_ms': execution_time_ms
            }
            
        except Exception as e:
            # Log error
            import traceback
            self.cache.log_error(
                agent_type=self.agent_type,
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                trace_id=trace_id,
                context={'revenue_data_keys': list(revenue_data.keys())},
                severity='high'
            )
            
            # End trace with error
            self.cache.end_trace(
                trace_id=trace_id,
                status='error',
                error_message=str(e)
            )
            
            raise
    
    def _generate_analysis(self, revenue_data: Dict[str, Any],
                          analysis_type: str, trace_id: str) -> Dict[str, Any]:
        """
        Generate revenue analysis using Gemini API with prompt caching.
        
        Args:
            revenue_data: Revenue data
            analysis_type: Type of analysis
            trace_id: Current trace ID
            
        Returns:
            Analysis results
        """
        # Construct prompt
        prompt = self._build_prompt(revenue_data, analysis_type)
        
        # Check prompt cache
        cached_prompt = self.cache.get_cached_prompt(prompt, self.model)
        
        if cached_prompt:
            print("  ✓ Prompt cache HIT")
            return json.loads(cached_prompt['response'])
        
        print("  ✗ Prompt cache MISS - calling Gemini API")
        
        # Simulate Gemini API call
        # In production, replace with actual Gemini API call
        response, tokens_input, tokens_output = self._call_gemini_api(prompt)
        
        # Cache the prompt response
        self.cache.cache_prompt(
            prompt=prompt,
            response=response,
            model=self.model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            ttl_hours=168  # 7 days for prompts
        )
        
        return json.loads(response)
    
    def _build_prompt(self, revenue_data: Dict[str, Any], analysis_type: str) -> str:
        """Build analysis prompt."""
        return f"""
Analyze the following SaaS revenue data and provide {analysis_type} analysis:

Data:
{json.dumps(revenue_data, indent=2)}

Provide analysis in JSON format with:
- mrr_trend: Description of MRR trajectory
- churn_analysis: Churn rate insights
- arpu_insights: Average revenue per user trends
- key_findings: List of critical findings
- recommendations: List of actionable recommendations
- risk_flags: Any concerning patterns

Ensure all findings are grounded in the provided data.
"""
    
    def _call_gemini_api(self, prompt: str) -> tuple[str, int, int]:
        """
        Simulate Gemini API call.
        
        In production, replace with actual Gemini API call:
        
        import google.generativeai as genai
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        
        Args:
            prompt: The prompt to send
            
        Returns:
            (response_text, input_tokens, output_tokens)
        """
        # Simulate API latency
        time.sleep(0.5)
        
        # Mock response
        mock_analysis = {
            "mrr_trend": "MRR showing 15% month-over-month growth, accelerating from Q3",
            "churn_analysis": "Churn rate at 3.2%, down from 4.1% last quarter. Improvement driven by better onboarding",
            "arpu_insights": "ARPU increased 8% to $127/user, primarily from upsells to higher tiers",
            "key_findings": [
                "Enterprise segment growing 25% faster than SMB",
                "Annual contracts showing 40% lower churn vs monthly",
                "Q4 pipeline suggests continued acceleration"
            ],
            "recommendations": [
                "Double down on enterprise sales motions",
                "Incentivize annual contract conversions",
                "Investigate SMB churn drivers for improvement opportunities"
            ],
            "risk_flags": [
                "SMB segment churn elevated at 5.8%",
                "Q1 renewals compressed into 3-week period - capacity risk"
            ]
        }
        
        response_text = json.dumps(mock_analysis)
        
        # Estimate token counts (in production, use actual counts)
        input_tokens = len(prompt.split()) * 1.3  # Rough estimate
        output_tokens = len(response_text.split()) * 1.3
        
        return response_text, int(input_tokens), int(output_tokens)
    
    def _calculate_confidence(self, revenue_data: Dict[str, Any],
                             analysis_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on data quality and completeness.
        
        Args:
            revenue_data: Input data
            analysis_result: Generated analysis
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 1.0
        
        # Reduce confidence if data is sparse
        records = revenue_data.get('records', [])
        if len(records) < 8:  # Less than 8 weeks
            confidence *= 0.8
        
        # Reduce confidence if key metrics are missing
        required_fields = ['mrr', 'churn_rate', 'arpu']
        for field in required_fields:
            if field not in revenue_data:
                confidence *= 0.9
        
        # Reduce confidence if analysis lacks key components
        required_analysis = ['mrr_trend', 'churn_analysis', 'recommendations']
        for field in required_analysis:
            if field not in analysis_result or not analysis_result[field]:
                confidence *= 0.85
        
        return round(confidence, 2)


def example_usage():
    """
    Example demonstrating Revenue Agent with CacheManager integration.
    """
    print("=" * 70)
    print("SaaS BI Agent - Revenue Agent Example")
    print("=" * 70)
    print()
    
    # Initialize cache manager
    cache = CacheManager(db_path="data/agent_cache.db")
    
    # Create session
    session_id = cache.create_session(session_type='weekly_review', user_id='demo_user')
    print(f"✓ Created session: {session_id}\n")
    
    # Sample revenue data
    revenue_data = {
        "period": "2025-Q4",
        "mrr": 1250000,
        "churn_rate": 3.2,
        "arpu": 127,
        "records": [
            {"week": 1, "mrr": 1150000, "new_customers": 45, "churned": 12},
            {"week": 2, "mrr": 1180000, "new_customers": 52, "churned": 10},
            {"week": 3, "mrr": 1200000, "new_customers": 48, "churned": 8},
            {"week": 4, "mrr": 1220000, "new_customers": 55, "churned": 11},
            {"week": 5, "mrr": 1235000, "new_customers": 49, "churned": 9},
            {"week": 6, "mrr": 1245000, "new_customers": 51, "churned": 7},
            {"week": 7, "mrr": 1248000, "new_customers": 46, "churned": 10},
            {"week": 8, "mrr": 1250000, "new_customers": 50, "churned": 8}
        ]
    }
    
    # Initialize agent
    agent = RevenueAgent(cache_manager=cache)
    
    # First analysis - should be cache MISS
    print("--- First Analysis (Cache MISS Expected) ---")
    result1 = agent.analyze(
        revenue_data=revenue_data,
        session_id=session_id,
        analysis_type="comprehensive"
    )
    print(f"Result: Cached={result1['cached']}, "
          f"Confidence={result1['confidence']}, "
          f"Time={result1.get('execution_time_ms', 'N/A')}ms")
    print(f"Analysis: {json.dumps(result1['analysis'], indent=2)[:200]}...")
    print()
    
    # Second analysis - should be cache HIT
    print("--- Second Analysis (Cache HIT Expected) ---")
    result2 = agent.analyze(
        revenue_data=revenue_data,
        session_id=session_id,
        analysis_type="comprehensive"
    )
    print(f"Result: Cached={result2['cached']}, Confidence={result2['confidence']}")
    print()
    
    # Different analysis type - should be cache MISS
    print("--- Different Analysis Type (Cache MISS Expected) ---")
    result3 = agent.analyze(
        revenue_data=revenue_data,
        session_id=session_id,
        analysis_type="trend_focused"
    )
    print(f"Result: Cached={result3['cached']}, Confidence={result3['confidence']}")
    print()
    
    # End session
    cache.end_session(session_id, final_status='completed')
    print(f"✓ Session ended: {session_id}\n")
    
    # Display cache stats
    print("--- Cache Performance ---")
    cache_stats = cache.get_cache_stats(days=1)
    if cache_stats:
        for stat in cache_stats:
            print(f"Date: {stat['date']}")
            print(f"  Total entries: {stat['total_entries']}")
            print(f"  Total hits: {stat['total_hits']}")
            print(f"  Hit rate: {stat['hit_rate_percent']:.1f}%")
            print(f"  Tokens saved: {stat['tokens_saved']}")
    print()
    
    # Display agent performance
    print("--- Agent Performance ---")
    perf = cache.get_agent_performance()
    for agent_perf in perf:
        print(f"Agent: {agent_perf['agent_type']}")
        print(f"  Invocations: {agent_perf['total_invocations']}")
        print(f"  Avg duration: {agent_perf['avg_duration_ms']:.0f}ms")
        print(f"  Success rate: {agent_perf['success_rate']:.1f}%")
        print(f"  Cache efficiency: {agent_perf.get('cache_efficiency_percent', 0):.1f}%")
    print()
    
    cache.close()
    print("=" * 70)
    print("✓ Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    example_usage()
