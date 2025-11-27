"""
ADK LoopAgent for Regeneration
Handles automatic regeneration when evaluation fails quality threshold.

This module creates a LoopAgent that wraps the SynthesizerAgent and EvaluationAgent
to automatically regenerate if quality score is below threshold.
"""

from typing import Optional
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types
from adk_agents.synthesizer_agent import create_synthesizer_agent
from adk_agents.evaluation_agent import create_evaluation_agent
from utils.logger import logger
from utils.config import config


def _check_evaluation_result(*, callback_context: CallbackContext) -> Optional[genai_types.Content]:
    """
    Callback to check evaluation result and determine if loop should continue.
    
    This callback is called after each iteration to check if the evaluation
    passed the quality threshold. If not, the loop continues.
    
    Args:
        callback_context: ADK CallbackContext with agent execution context (must be keyword argument)
        
    Returns:
        None to continue loop, or Content to stop loop
    """
    try:
        # Extract evaluation result from context
        # The evaluation agent's output should be in the context messages
        context = callback_context  # Use callback_context internally
        if hasattr(context, 'messages') and context.messages:
            # Get the last message which should be from evaluation agent
            last_message = context.messages[-1]
            if hasattr(last_message, 'content'):
                content = last_message.content
                
                # Parse evaluation result
                import json
                if isinstance(content, str):
                    eval_result = json.loads(content)
                elif hasattr(content, 'parts') and content.parts:
                    # Extract text from Content parts
                    text_parts = [p.text for p in content.parts if hasattr(p, 'text')]
                    if text_parts:
                        eval_result = json.loads(text_parts[0])
                    else:
                        return None
                else:
                    eval_result = content if isinstance(content, dict) else {}
                
                # Check if evaluation passed
                overall_score = eval_result.get('overall_score', 0.0)
                pass_threshold = eval_result.get('pass_threshold', False)
                regeneration_needed = eval_result.get('regeneration_needed', True)
                
                quality_threshold = config.get('evaluation.quality_threshold', 0.75)
                
                # If evaluation passed, stop the loop by returning a Content object
                # Returning None continues the loop, returning Content may stop it
                # Note: LoopAgent will also respect max_iterations as a safety limit
                if pass_threshold and overall_score >= quality_threshold and not regeneration_needed:
                    logger.info(f"Evaluation passed with score {overall_score:.2f}, stopping regeneration loop")
                    # Return Content to signal loop should stop
                    # ADK LoopAgent may interpret Content return as "done"
                    stop_signal = genai_types.Content(
                        parts=[genai_types.Part(text=json.dumps({"loop_stop": True, "reason": "evaluation_passed"}))],
                        role="assistant"
                    )
                    return stop_signal
                else:
                    logger.info(f"Evaluation failed with score {overall_score:.2f}, continuing regeneration loop")
                    # Return None to continue loop
                    return None
                    
    except Exception as e:
        logger.error(f"Error checking evaluation result: {e}", exc_info=True)
        # On error, continue loop (safer)
        return None
    
    # Default: continue loop
    return None


def create_regeneration_loop() -> LoopAgent:
    """
    Create ADK LoopAgent for automatic regeneration when evaluation fails.
    
    This LoopAgent wraps:
    1. SynthesizerAgent: Generates synthesized report
    2. EvaluationAgent: Evaluates quality
    
    The loop continues until:
    - Evaluation passes quality threshold (default: 0.75)
    - Max iterations reached (default: 3)
    
    Architecture:
    ```
    LoopAgent (Regeneration Loop)
    └── SequentialAgent (Synthesis Pipeline)
        ├── SynthesizerAgent (Generate report)
        └── EvaluationAgent (Evaluate quality)
    ```
    
    Returns:
        Configured LoopAgent instance for regeneration
    """
    # Create sub-agents
    synthesizer_agent = create_synthesizer_agent()
    evaluation_agent = create_evaluation_agent()
    
    # Get configuration
    max_iterations = config.get('evaluation.max_regeneration_iterations', 3)
    quality_threshold = config.get('evaluation.quality_threshold', 0.75)
    
    # Create a SequentialAgent to ensure Synthesizer runs BEFORE Evaluation
    # This is critical: Evaluation needs the synthesized report to evaluate
    synthesis_pipeline = SequentialAgent(
        name="synthesis_pipeline",
        description="Sequential pipeline: Synthesizer generates report, then Evaluation validates quality",
        sub_agents=[
            synthesizer_agent,  # First: Generate synthesized report
            evaluation_agent,   # Second: Evaluate quality (waits for synthesizer)
        ]
    )
    
    # Create LoopAgent wrapping the sequential pipeline
    # The loop will re-run the entire pipeline if evaluation fails
    loop_agent = LoopAgent(
        name="regeneration_loop",
        description=f"Automatic regeneration loop: runs synthesis pipeline, regenerates if score < {quality_threshold}",
        sub_agents=[synthesis_pipeline],  # Single sub-agent: the sequential pipeline
        max_iterations=max_iterations,
        after_agent_callback=_check_evaluation_result  # Check after evaluation if we should continue
    )
    
    logger.info(f"ADK Regeneration LoopAgent created with max_iterations={max_iterations}, threshold={quality_threshold}")
    
    return loop_agent

